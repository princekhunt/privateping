import json

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from chat.consumers import ChatConsumer, ChatConsumerCurrentStatus, ChatConsumerNotify
from chat.models import Friends, Keys, UserProfile
from chat.tools import are_friends
from registration.models import user_type


import base64 as _b64

def _b64u(n):
    return _b64.urlsafe_b64encode(b"\x01" * n).rstrip(b"=").decode()

MID = "0123456789abcdef0123456789abcdef"

ENC_JWK = json.dumps({"kty": "RSA", "n": _b64u(256), "e": "AQAB", "alg": "RSA-OAEP-256"})
SIG_JWK = json.dumps({"kty": "EC", "crv": "P-256", "x": _b64u(32), "y": _b64u(32)})


def make_user(username):
    user = User.objects.create_user(username=username, password="pw-" + username + "-X1!")
    profile = UserProfile.objects.create(user=user, name=username, username=username)
    user_type.objects.create(user=user, type="regular")
    Keys.objects.create(user=profile, public_key=ENC_JWK, signing_key=SIG_JWK)
    return user, profile


def befriend(a, b):
    Friends.objects.create(user=a, friend=b, accepted=True)
    Friends.objects.create(user=b, friend=a, accepted=True)


class FriendshipViewTests(TestCase):
    def setUp(self):
        self.alice_u, self.alice = make_user("alice_victim")
        self.bob_u, self.bob = make_user("bob_attacker")
        self.carol_u, self.carol = make_user("carol_friend")
        befriend(self.alice, self.carol)

    def test_are_friends(self):
        self.assertTrue(are_friends(self.alice, self.carol))
        self.assertFalse(are_friends(self.alice, self.bob))
        self.assertFalse(are_friends(self.alice, self.alice))

    def test_pending_request_is_not_friendship(self):
        Friends.objects.create(user=self.bob, friend=self.alice, accepted=True)
        Friends.objects.create(user=self.alice, friend=self.bob, accepted=False)
        self.assertFalse(are_friends(self.bob, self.alice))

    def test_non_friend_cannot_get_public_key(self):
        self.client.force_login(self.bob_u)
        r = self.client.get("/chat/alice_victim")
        self.assertEqual(r.status_code, 302)
        self.assertNotIn("public_key", r.cookies)

    def test_friend_gets_public_key(self):
        self.client.force_login(self.carol_u)
        r = self.client.get("/chat/alice_victim")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="pp-friend-keys"')
        self.assertContains(r, json.loads(ENC_JWK)["n"])

    def test_non_friend_page_has_no_key(self):
        self.client.force_login(self.bob_u)
        r = self.client.get("/chat/alice_victim", follow=True)
        self.assertNotContains(r, json.loads(ENC_JWK)["n"])

    def test_chat_requires_signing_key(self):
        Keys.objects.filter(user=self.alice).update(signing_key="")
        self.client.force_login(self.carol_u)
        self.assertEqual(self.client.get("/chat/alice_victim").status_code, 302)

    def test_hostile_display_name_is_escaped(self):
        self.carol.name = "');alert(1);//<b>"
        self.carol.save()
        self.client.force_login(self.alice_u)
        r = self.client.get("/dashboard")
        html = r.content.decode()
        self.assertNotIn("<b>", html.split("pp-friend-name")[1][:200])
        self.assertNotIn("onclick", html)

    def test_pages_have_strict_csp(self):
        self.client.force_login(self.alice_u)
        r = self.client.get("/dashboard")
        csp = r["Content-Security-Policy"]
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("https://", csp)  # no third-party origins at all
        self.assertNotIn("unsafe-eval", csp)
        self.assertIn("frame-ancestors 'self'", csp)
        self.assertEqual(r["X-Frame-Options"], "SAMEORIGIN")
        self.assertNotIn("<script>", r.content.decode())

    def test_anonymous_cannot_open_chat(self):
        r = self.client.get("/chat/alice_victim")
        self.assertEqual(r.status_code, 302)

    def test_add_friend_get_does_not_create_request(self):
        self.client.force_login(self.bob_u)
        r = self.client.get("/addfriend/alice_victim?note=hi")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Friends.objects.filter(user=self.bob, friend=self.alice).exists())

    def test_add_friend_post_requires_csrf(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.bob_u)
        r = c.post("/addfriend/alice_victim", {"note": "hi"})
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Friends.objects.filter(user=self.bob, friend=self.alice).exists())

    def test_add_friend_post_creates_pending_request(self):
        self.client.force_login(self.bob_u)
        self.client.post("/addfriend/alice_victim", {"note": "hi"})
        self.assertTrue(Friends.objects.filter(user=self.alice, friend=self.bob, accepted=False).exists())
        self.assertFalse(are_friends(self.bob, self.alice))

    def test_cannot_add_self(self):
        self.client.force_login(self.bob_u)
        self.client.post("/addfriend/bob_attacker")
        self.assertFalse(Friends.objects.filter(user=self.bob, friend=self.bob).exists())

    def test_delete_friend_requires_post(self):
        self.client.force_login(self.alice_u)
        r = self.client.get("/delete_friend?friend=carol_friend")
        self.assertEqual(r.status_code, 405)
        self.assertTrue(are_friends(self.alice, self.carol))
        r = self.client.post("/delete_friend", {"friend": "carol_friend"})
        self.assertEqual(r.json()["status"], True)
        self.assertFalse(are_friends(self.alice, self.carol))

    def test_friend_request_accept_flow(self):
        self.client.force_login(self.bob_u)
        self.client.post("/addfriend/alice_victim", {"note": "<script>x</script>"})
        self.client.force_login(self.alice_u)
        r = self.client.get("/request?user=bob_attacker")
        self.assertContains(r, "&lt;script&gt;x&lt;/script&gt;")
        r = self.client.post("/request", {"request_from": "bob_attacker", "action": "accept"})
        self.assertEqual(r.json()["status"], True)
        self.assertTrue(are_friends(self.alice, self.bob))

    def test_cannot_accept_nonexistent_request(self):
        self.client.force_login(self.bob_u)
        r = self.client.post("/request", {"request_from": "alice_victim", "action": "accept"})
        self.assertEqual(r.status_code, 404)
        self.assertFalse(are_friends(self.alice, self.bob))

    def test_friends_partial_shows_states(self):
        Friends.objects.create(user=self.bob, friend=self.alice, accepted=True)
        Friends.objects.create(user=self.alice, friend=self.bob, accepted=False)
        self.client.force_login(self.alice_u)
        r = self.client.get("/api/friends")
        self.assertContains(r, "pp-friend-incoming")
        self.assertContains(r, "Friend requests")
        self.assertContains(r, "pp-friend-friends")
        self.client.force_login(self.bob_u)
        self.assertContains(self.client.get("/api/friends"), "Sent requests")

    def test_dashboard_greeting_is_static(self):
        self.client.force_login(self.alice_u)
        r = self.client.get("/dashboard")
        self.assertContains(r, "Hello, alice_victim")
        self.assertNotContains(r, "changeTxt")

    def test_room_api_requires_friendship(self):
        self.bob.online = 1
        self.bob.online_for = self.alice
        self.bob.save()
        self.client.force_login(self.alice_u)
        self.assertFalse(self.client.get("/api/room?user=bob_attacker").json()["status"])


class RelayTests(TransactionTestCase):
    def setUp(self):
        self.alice_u, self.alice = make_user("alice_victim")
        self.bob_u, self.bob = make_user("bob_attacker")
        self.carol_u, self.carol = make_user("carol_friend")
        befriend(self.alice, self.carol)

    async def _connect(self, consumer, user):
        comm = WebsocketCommunicator(consumer.as_asgi(), "/ws/chat/")
        comm.scope["user"] = user
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        return comm

    def test_non_friend_message_is_not_relayed(self):
        async def run():
            alice = await self._connect(ChatConsumer, self.alice_u)
            bob = await self._connect(ChatConsumer, self.bob_u)
            await bob.send_to(text_data=json.dumps(
                {"message": "Y2lwaGVydGV4dA==", "to": "alice_victim", "destroy": "0", "mid": MID}))
            reply = json.loads(await bob.receive_from())
            self.assertEqual(reply["status"], "error")
            self.assertEqual(reply["mid"], MID)  # sender marks it "Not delivered", never "Sent"
            # non-friends can't send receipts or presence either
            await bob.send_to(text_data=json.dumps({"receipt": '{"r":"x","s":"y"}', "to": "alice_victim"}))
            await bob.send_to(text_data=json.dumps({"ready": True, "to": "alice_victim"}))
            self.assertTrue(await alice.receive_nothing(timeout=0.3))
            await alice.disconnect()
            await bob.disconnect()
        async_to_sync(run)()

    def test_friend_message_is_relayed_with_sender(self):
        async def run():
            alice = await self._connect(ChatConsumer, self.alice_u)
            carol = await self._connect(ChatConsumer, self.carol_u)
            await carol.send_to(text_data=json.dumps(
                {"message": "Y2lwaGVydGV4dA==", "to": "alice_victim", "destroy": "10", "mid": MID}))
            got = json.loads(await alice.receive_from())
            self.assertEqual(got["from"], "carol_friend")
            self.assertEqual(got["destroy"], 10)
            self.assertEqual(got["mid"], MID)
            ack = json.loads(await carol.receive_from())
            self.assertEqual(ack, {"status": "accepted", "mid": MID})

            # receipts and presence are relayed between friends, tagged with the sender
            await alice.send_to(text_data=json.dumps({"receipt": '{"r":"x","s":"y"}', "to": "carol_friend"}))
            got = json.loads(await carol.receive_from())
            self.assertEqual(got, {"status": "receipt", "receipt": '{"r":"x","s":"y"}', "from": "alice_victim"})
            await alice.send_to(text_data=json.dumps({"ready": True, "to": "carol_friend"}))
            got = json.loads(await carol.receive_from())
            self.assertEqual(got, {"status": "ready", "reply": False, "from": "alice_victim"})
            await alice.disconnect()
            await carol.disconnect()
        async_to_sync(run)()

    def test_non_friend_cannot_set_online_for(self):
        async def run():
            bob = await self._connect(ChatConsumerCurrentStatus, self.bob_u)
            await bob.send_to(text_data=json.dumps({"status": "typing", "for": "alice_victim"}))
            await bob.receive_nothing(timeout=0.3)
            await bob.disconnect()
        async_to_sync(run)()
        self.bob.refresh_from_db()
        self.assertIsNone(self.bob.online_for)

    def test_message_without_valid_id_rejected(self):
        async def run():
            carol = await self._connect(ChatConsumer, self.carol_u)
            for bad in [None, "short", "Z" * 32, MID.upper()]:
                await carol.send_to(text_data=json.dumps(
                    {"message": "Y2lwaGVydGV4dA==", "to": "alice_victim", "destroy": 0, "mid": bad}))
                self.assertEqual(json.loads(await carol.receive_from())["status"], "error")
            await carol.disconnect()
        async_to_sync(run)()

    def test_oversized_message_rejected(self):
        async def run():
            alice = await self._connect(ChatConsumer, self.alice_u)
            carol = await self._connect(ChatConsumer, self.carol_u)
            await carol.send_to(text_data=json.dumps(
                {"message": "A" * 20000, "to": "alice_victim", "destroy": 0}))
            reply = json.loads(await carol.receive_from())
            self.assertEqual(reply["status"], "error")
            self.assertTrue(await alice.receive_nothing(timeout=0.3))
            await alice.disconnect()
            await carol.disconnect()
        async_to_sync(run)()

    def test_flood_is_dropped(self):
        async def run():
            alice = await self._connect(ChatConsumer, self.alice_u)
            carol = await self._connect(ChatConsumer, self.carol_u)
            for _ in range(60):
                await carol.send_to(text_data=json.dumps(
                    {"message": "Y2lwaGVydGV4dA==", "to": "alice_victim", "destroy": 0, "mid": MID}))
            got = 0
            while not await alice.receive_nothing(timeout=0.2):
                await alice.receive_from()
                got += 1
            self.assertLess(got, 70)
            await alice.disconnect()
            await carol.disconnect()
        async_to_sync(run)()

    def test_cross_origin_websocket_rejected(self):
        from PrivatePing.asgi import application

        async def run():
            comm = WebsocketCommunicator(application, "/ws/chat/",
                                         headers=[(b"origin", b"https://evil.example"), (b"host", b"localhost")])
            connected, _ = await comm.connect()
            self.assertFalse(connected)
        async_to_sync(run)()

    def test_friend_request_is_pushed_live(self):
        from django.test import Client

        async def connect_alice():
            return await self._connect(ChatConsumerNotify, self.alice_u)

        async def run():
            alice = await connect_alice()
            # Bob sends a request through the normal HTTP view (sync, in a thread)
            from asgiref.sync import sync_to_async

            def send_request():
                c = Client()
                c.force_login(self.bob_u)
                c.post("/addfriend/alice_victim", {"note": "hi"})
            await sync_to_async(send_request)()
            got = json.loads(await alice.receive_from(timeout=2))
            self.assertEqual(got, {"status": "friends", "event": "request", "from": "bob_attacker"})
            await alice.disconnect()
        async_to_sync(run)()

    def test_unauthenticated_socket_is_rejected(self):
        from django.contrib.auth.models import AnonymousUser

        async def run():
            comm = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            comm.scope["user"] = AnonymousUser()
            connected, _ = await comm.connect()
            self.assertFalse(connected)
        async_to_sync(run)()


class DeclineCooldownTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.alice_u, self.alice = make_user("alice_victim")
        self.carol_u, self.carol = make_user("carol_friend")
        befriend(self.alice, self.carol)

    def _wait_for_carol(self):
        # Alice sits in the waiting room for Carol
        self.alice.online = 1
        self.alice.online_for = self.carol
        self.alice.save()

    def _decline_as_carol(self):
        self.client.force_login(self.carol_u)
        return self.client.post("/api/decline_chat", {"user": "alice_victim"}).json()

    def test_cooldown_grows_progressively(self):
        from chat import cooldown
        waits = [cooldown.record_decline("chat", "a", "b") for _ in range(7)]
        self.assertEqual(waits[:5], cooldown.STEPS)
        self.assertEqual(waits[5:], [cooldown.STEPS[-1]] * 2)  # capped
        self.assertTrue(all(x < y for x, y in zip(waits[:5], waits[1:5])))
        cooldown.clear("chat", "b", "a")
        self.assertEqual(cooldown.remaining("chat", "a", "b"), 0)

    def test_decline_tells_waiter_and_blocks_retry(self):
        from unittest import mock
        self._wait_for_carol()
        with mock.patch("chat.views.push_to_user") as push:
            r = self._decline_as_carol()
        self.assertTrue(r["status"])
        self.assertEqual(r["retry_in"], 120)
        push.assert_called_once()
        user, event = push.call_args.args
        self.assertEqual(user, "alice_victim")
        self.assertEqual(event["type"], "chat_declined")
        self.assertEqual(event["from"], "carol_friend")
        self.assertEqual(event["retry_text"], "2 minutes")
        self.alice.refresh_from_db()
        self.assertIsNone(self.alice.online_for)

        # Alice can't go straight back into the waiting room
        self.client.force_login(self.alice_u)
        r = self.client.get("/waiting-room?user=carol_friend", follow=True)
        self.assertContains(r, "try again in 2 minutes")

        # Second decline -> longer wait
        from chat import cooldown
        cooldown.record_decline  # noqa
        from django.core.cache import cache
        key = "cooldown:chat:alice_victim:carol_friend"
        state = cache.get(key); state["until"] = 0; cache.set(key, state)  # first cool-down over
        self._wait_for_carol()
        self.assertEqual(self._decline_as_carol()["retry_in"], 300)

    def test_waiting_room_allowed_if_they_wait_for_us(self):
        self._wait_for_carol()
        self._decline_as_carol()
        self.carol.online = 1
        self.carol.online_for = self.alice
        self.carol.save()
        self.client.force_login(self.alice_u)
        self.assertEqual(self.client.get("/waiting-room?user=carol_friend").status_code, 200)

    def test_cannot_decline_someone_not_waiting(self):
        r = self._decline_as_carol()
        self.assertFalse(r["status"])

    def test_successful_chat_clears_strikes(self):
        from chat import cooldown
        cooldown.record_decline("chat", "alice_victim", "carol_friend")
        self.client.force_login(self.alice_u)
        self.client.get("/chat/carol_friend")
        self.assertEqual(cooldown.strikes("chat", "alice_victim", "carol_friend"), 0)

    def test_rejected_friend_request_has_cooldown(self):
        bob_u, bob = make_user("bob_attacker")
        c = self.client
        c.force_login(bob_u)
        c.post("/addfriend/alice_victim")
        c.force_login(self.alice_u)
        c.post("/request", {"request_from": "bob_attacker", "action": "reject"})
        c.force_login(bob_u)
        r = c.post("/addfriend/alice_victim", follow=True)
        self.assertContains(r, "send another one in 2 minutes")
        self.assertFalse(Friends.objects.filter(user=bob, friend=self.alice).exists())


class DeclinePushTests(TransactionTestCase):
    def test_waiting_user_gets_live_decline(self):
        from asgiref.sync import sync_to_async
        from django.core.cache import cache
        from django.test import Client
        cache.clear()
        alice_u, alice = make_user("alice_victim")
        carol_u, carol = make_user("carol_friend")
        befriend(alice, carol)
        UserProfile.objects.filter(pk=alice.pk).update(online=1, online_for=carol)

        async def run():
            comm = WebsocketCommunicator(ChatConsumerNotify.as_asgi(), "/ws/notify/")
            comm.scope["user"] = alice_u
            await comm.connect()

            def decline():
                c = Client()
                c.force_login(carol_u)
                c.post("/api/decline_chat", {"user": "alice_victim"})
            await sync_to_async(decline)()
            got = json.loads(await comm.receive_from(timeout=2))
            self.assertEqual(got["status"], "declined")
            self.assertEqual(got["from"], "carol_friend")
            self.assertEqual(got["retry_text"], "2 minutes")
            await comm.disconnect()
        async_to_sync(run)()

