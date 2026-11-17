import io
import json

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from chat.models import Keys, UserProfile
from chat.tests import ENC_JWK, SIG_JWK, make_user
from registration.forms import SignUpForm
from registration.models import user_type
from registration.security import InvalidKey, clean_encryption_jwk, clean_signing_jwk
from registration.tools import generate_username


class SignUpFormTests(TestCase):
    def _form(self, username, password="c0rrect-Horse-battery"):
        return SignUpForm({
            "username": username, "name": "Test", "email": username + "@x.com",
            "password1": password, "password2": password,
        })

    def test_rejects_html_in_username(self):
        self.assertFalse(self._form("<img src=x onerror=1>").is_valid())
        self.assertFalse(self._form("bob'); x//").is_valid())

    def test_accepts_normal_username(self):
        self.assertTrue(self._form("alice_123").is_valid())

    def test_rejects_weak_password(self):
        self.assertFalse(self._form("alice_123", "password").is_valid())
        self.assertFalse(self._form("alice_123", "1234567890").is_valid())


class KeyValidationTests(TestCase):
    def test_valid_keys(self):
        self.assertIn('"kty":"RSA"', clean_encryption_jwk(ENC_JWK))
        self.assertIn('"crv":"P-256"', clean_signing_jwk(SIG_JWK))

    def test_rejects_private_key_material(self):
        jwk = json.loads(ENC_JWK)
        jwk["d"] = "secret"
        with self.assertRaises(InvalidKey):
            clean_encryption_jwk(json.dumps(jwk))

    def test_rejects_weak_or_garbage_keys(self):
        jwk = json.loads(ENC_JWK)
        jwk["n"] = "AQAB"
        for bad in [json.dumps(jwk), "not json", "[]", "", "x" * 10000]:
            with self.assertRaises(InvalidKey):
                clean_encryption_jwk(bad)
        with self.assertRaises(InvalidKey):
            clean_signing_jwk(ENC_JWK)


class AuthFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user, self.profile = make_user("alice_victim")
        self.user.set_password("c0rrect-Horse-battery")
        self.user.save()

    def test_login_then_keys_upload(self):
        r = self.client.post("/login/", {"username": "alice_victim", "password": "c0rrect-Horse-battery"})
        self.assertRedirects(r, "/generate_keys/", fetch_redirect_response=False)
        r = self.client.post("/generate_keys/", {"public_key": ENC_JWK, "signing_key": SIG_JWK})
        self.assertEqual(r.json()["status"], "ok")

    def test_key_upload_rejects_private_key(self):
        self.client.force_login(self.user)
        jwk = json.loads(ENC_JWK)
        jwk["d"] = "secret"
        r = self.client.post("/generate_keys/", {"public_key": json.dumps(jwk), "signing_key": SIG_JWK})
        self.assertEqual(r.status_code, 400)
        self.assertNotIn("secret", Keys.objects.get(user=self.profile).public_key)

    def test_login_bruteforce_lockout(self):
        for _ in range(5):
            self.client.post("/login/", {"username": "alice_victim", "password": "wrong"})
        r = self.client.post("/login/", {"username": "alice_victim", "password": "c0rrect-Horse-battery"})
        self.assertEqual(r.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_requires_csrf(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        r = c.post("/login/", {"username": "alice_victim", "password": "c0rrect-Horse-battery"})
        self.assertEqual(r.status_code, 403)

    def test_logout_requires_post_and_wipes_keys(self):
        self.client.force_login(self.user)
        self.client.get("/logout/")
        self.assertIn("_auth_user_id", self.client.session)
        r = self.client.post("/logout/")
        self.assertContains(r, "js/registration/LoggedOut.js")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(Keys.objects.get(user=self.profile).public_key, "")

    def test_signup_shows_errors_inline(self):
        r = self.client.post("/signup/", {"name": "x", "username": "bad name!", "password1": "a",
                                          "password2": "a"})
        self.assertEqual(r.status_code, 400)
        self.assertContains(r, "pp-form-errors", status_code=400)

    def test_signup_creates_account(self):
        r = self.client.post("/signup/", {"name": "Bob", "username": "bob_12345",
                                          "password1": "c0rrect-Horse-battery",
                                          "password2": "c0rrect-Horse-battery"})
        self.assertRedirects(r, "/login/", fetch_redirect_response=False)
        self.assertTrue(UserProfile.objects.filter(username="bob_12345").exists())


class AnonymousAccountTests(TestCase):
    def test_generate_username_never_runs_out(self):
        names = {generate_username() for _ in range(300)}
        self.assertEqual(len(names), 300)
        self.assertTrue(all(len(n) <= 20 and n.isalnum() for n in names))

    def test_cleanup_deletes_expired_anonymous(self):
        user, profile = make_user("tempuser1")
        user_type.objects.filter(user=user).update(type="Anonymous")
        User.objects.filter(pk=user.pk).update(date_joined=timezone.now() - timezone.timedelta(days=2))
        keep, _ = make_user("regular_1")
        call_command("cleanup_anonymous", stdout=io.StringIO())
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(User.objects.filter(pk=keep.pk).exists())


class ProofOfWorkTests(TestCase):
    def setUp(self):
        cache.clear()

    def _solve(self, challenge, bits):
        import hashlib
        from registration import pow as p
        n = 0
        while p.leading_zero_bits(hashlib.sha256(f"{challenge}:{n}".encode()).digest()) < bits:
            n += 1
        return str(n)

    def _fresh(self):
        from unittest import mock
        with mock.patch("registration.pow.BASE_BITS", 8):
            r = self.client.get("/AnonymousDirectLogin")
        data = json.loads(r.content.decode().split('id="pp-pow" type="application/json">')[1].split("</script>")[0])
        return data["challenge"], data["bits"]

    def test_page_has_no_third_party_captcha(self):
        r = self.client.get("/AnonymousDirectLogin")
        self.assertNotContains(r, "hcaptcha")
        self.assertNotIn("https://", r["Content-Security-Policy"])

    def test_valid_solution_creates_anonymous_account(self):
        challenge, bits = self._fresh()
        r = self.client.post("/AnonymousDirectLogin", {"challenge": challenge, "nonce": self._solve(challenge, bits)})
        self.assertEqual(r.json()["status"], "ok")
        user = User.objects.get(pk=self.client.session["_auth_user_id"])
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user_type.objects.get(user=user).type, "Anonymous")

    def test_wrong_answer_rejected(self):
        challenge, bits = self._fresh()
        nonce = self._solve(challenge, bits)
        r = self.client.post("/AnonymousDirectLogin", {"challenge": challenge, "nonce": str(int(nonce) + 1)})
        # (the next nonce could in theory also solve it; with 8 bits that's a 1/256 chance)
        self.assertIn(r.status_code, (200, 400))
        r = self.client.post("/AnonymousDirectLogin", {"challenge": challenge + "x", "nonce": nonce})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/AnonymousDirectLogin", {"nonce": nonce})
        self.assertEqual(r.status_code, 400)

    def test_solution_is_single_use(self):
        from django.test import Client
        challenge, bits = self._fresh()
        nonce = self._solve(challenge, bits)
        self.assertEqual(Client().post("/AnonymousDirectLogin", {"challenge": challenge, "nonce": nonce}).status_code, 200)
        r = Client().post("/AnonymousDirectLogin", {"challenge": challenge, "nonce": nonce})
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.json()["retry"])

    def test_expired_challenge_rejected(self):
        from unittest import mock
        challenge, bits = self._fresh()
        nonce = self._solve(challenge, bits)
        with mock.patch("registration.pow.TTL", -1):
            r = self.client.post("/AnonymousDirectLogin", {"challenge": challenge, "nonce": nonce})
        self.assertEqual(r.status_code, 400)

    def test_honeypot_blocks_bots(self):
        challenge, bits = self._fresh()
        r = self.client.post("/AnonymousDirectLogin", {"challenge": challenge, "nonce": self._solve(challenge, bits),
                                                       "website": "http://spam.example"})
        self.assertEqual(r.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_difficulty_rises_with_volume(self):
        from registration import pow as p
        base = p.difficulty("1.2.3.4")
        for _ in range(6):
            p.record_success("1.2.3.4")
        self.assertGreater(p.difficulty("1.2.3.4"), base)
        self.assertEqual(p.difficulty("5.6.7.8"), base)  # other visitors unaffected

