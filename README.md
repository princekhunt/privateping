<div align="center">
  <img src="/assets/images/logo/png/logo-color.png" alt="PrivatePing Logo" width=50%>
  <h1>PrivatePing - A Secure Messaging Application</h1>
</div>

[![Website Status](https://img.shields.io/website?url=https%3A%2F%2Fprivateping.plutoweb.live)](https://privateping.plutoweb.live)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PrivatePing is a secure messaging application built on Python's Django framework, providing end-to-end encryption for messages exchanged between users. It leverages HTML, CSS, JavaScript, SubtleCrypto API, channels, and Redis to ensure secure communication channels.

## Features

- **End-to-End Encryption**: Messages are encrypted using SubtleCrypto API in JavaScript. It uses SHA-256 algorithm, ensuring that only the intended recipient can decrypt and read the messages.
- **No Message Storage**: PrivatePing does not store messages on its servers, ensuring user privacy and confidentiality.
- **Anonymous Login**: Offers an anonymous login feature, creating temporary user accounts valid for 24 hours, enhancing privacy and security for users.
- **Secure Authentication**: Utilizes Django's default authentication mechanism to ensure secure user authentication and authorization.

**Note**: Currently, the application is not accessible from mobile and tablet devices. 

## Usage

PrivatePing is hosted on Heroku. It is accessible through a web browser. Users can register, log in securely, and exchange encrypted messages with each other without the need to install or run the application locally.

To get started:
1. Visit [PrivatePing](https://privateping.plutoweb.live) in your web browser.
2. You can either:
   - Sign up for a standard account using your email address, and Login using your credentials to continue.
   - Alternatively, use the option for anonymous direct login, which creates a temporary account for you valid for the next 24 hours. No private information will be attached to this account.
3. After successfully logging into the account, share your username with your friend to get started.
4. Click on the "Add User" button on the navigation bar at the top left.
5. Enter your friend's username and click on "Add".
6. Note that your friend will also need to add you on their dashboard using the same steps.
7. Once added, click on the user's name you wish to chat with.
8. PrivatePing will create a secure room for you both and wait for the other person to connect.
9. When you and your friend are successfully connected over a secure channel, you can start exchanging encrypted messages, which not even PrivatePing can decipher.

## How It Works

PrivatePing employs a robust encryption system to ensure secure and private communication between users. Here's a step-by-step breakdown of the process:

1. **User Authentication and Key Generation**: When a user logs into their account or creates a temporary account, PrivatePing's SubtleCrypto module generates a secure key-pair for the user. The private key is stored locally in the user's browser's local storage, while the public key is sent to the server. This key generation process occurs each time a user logs in, and any previous session keys are destroyed to maintain security.

2. **Initiating Communication**: When a user initiates communication with another user, PrivatePing fetches the recipient's public key from the server. This public key is then stored in the user's browser's cookie, awaiting connection. The same process occurs for the recipient user on the other side.

3. **Secure Connection Establishment**: Once both users are connected, PrivatePing establishes a secure and private communication channel between them.

4. **Message Encryption and Transmission**: When a user types a message and hits the send button, PrivatePing retrieves the recipient's public key from its cookie. The message is then encrypted using the SHA-256 algorithm and sent to the recipient over websockets.

5. **Message Decryption and Display**: Upon receiving the encrypted message, the recipient retrieves their private key from their browser's local storage. Using this private key, the recipient decrypts the message, which is then displayed on the webpage in its original form.

This comprehensive encryption process ensures that all communication on PrivatePing remains secure and private, with messages encrypted end-to-end and inaccessible to anyone other than the intended recipient.

## Contributors

We extend our heartfelt gratitude to all contributors who have helped improve PrivatePing! Your efforts are greatly appreciated. See the [humans.txt](https://privateping.plutoweb.live/humans.txt) page for a list of contributors.

Contributions are welcome! If you'd like to contribute to PrivatePing, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and ensure the code follows the project's coding standards.
4. Submit a pull request with a clear description of your changes.

We invite everyone to use this absolutely free application and suggest improvements that can enhance security and privacy.

## License

<<<<<<< HEAD
PrivatePing is licensed under the [MIT License](LICENSE).
=======
PrivatePing is licensed under the [MIT License](LICENSE).
>>>>>>> 7fc0cc00cdc8186dbf8b1ff4ca27f126d8b75c7d
