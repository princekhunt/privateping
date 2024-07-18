<div align="center">
  <img src="/assets/images/logo/png/logo-color.png" alt="PrivatePing Logo" width=50%>
  <h1>PrivatePing - A Secure Messaging Application</h1>
</div>

[![Website Status](https://img.shields.io/website?url=https%3A%2F%2Fprivateping.bytespot.tech)](https://privateping.bytespot.tech)
[![first-timers](https://img.shields.io/badge/first--timers--friendly-blue.svg?style=flat-square)](https://www.firsttimersonly.com/)
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
1. Visit [PrivatePing](https://privateping.bytespot.tech) in your web browser.
2. You can either:
   - Sign up for a standard account using your email address, and Login using your credentials to continue.
   - Alternatively, use the option for anonymous direct login, which creates a temporary account for you valid for the next 24 hours. No private information will be attached to this account.
3. After successfully logging into the account, click on "Add User" button on the navigation bar at the top left.
4. Enter your friend's username and click on "Add". A friend request will be sent to your friend.
5. Your friend will be able to see upcoming request from you, and can accept or reject the request.
6. If a friend accepts the request, then you will be able to chat.
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

## Local Installation

### Linux and Mac
You can install PrivatePing locally on Linux and Mac devices using the provided installation script.

1. Clone the repository.
2. Open a terminal window.
3. Navigate to the directory where the `install.sh` script is located.
4. Run the following command to make the script executable:
   ```bash
   chmod +x install.sh
5. Eecute the script by running:
   ```bash
   ./install.sh

### Windows (Alternative Method for Linux and Mac)

If you prefer not to use the provided installation script or encounter any issues, you can manually install PrivatePing on Linux and Mac using the following steps:

1. **Install Python 3:** If you haven't already, install Python 3 on your system. You can download it from [Python's official website](https://www.python.org/downloads/).

2. **Install Virtualenv:** This command installs Virtualenv, a tool used to create isolated Python environments.
   ```bash
   pip3 install virtualenv
3. **Clone the repository with the following command:**
   ```bash
   git clone https://github.com/princekhunt/privateping.git
4. **Create a Virtual Environment:** This command creates a virtual environment named `venv` in the current directory.
   ```bash
   python3 -m venv venv
5. **Activate the Virtual Environment:** Activating the virtual environment isolates your Python environment, ensuring dependencies are installed locally rather than globally.
   - If you are using linux or mac, Activate virtual environment using:
     ```bash
     source venv/bin/activate
   - If you are using windows, Activate virtual environment using:
     ```bash
     venv\Scripts\activate

7. **Install Dependencies:** This command installs all required Python packages specified in the `requirements.txt` file.
   ```bash
   pip3 install -r requirements.txt
8. **Create `.env` File:** These commands create a .env file in the `PrivatePing/settings` directory with environment variable configurations. (Recommendation: Generate a new SECRET_KEY and replace it with the defined here.)
   ```bash
   echo "SECRET_KEY='*$j@tpltfyblml&*1d+n9t@il^0xef4=bvdu&!7r=zvoq$a19g'" > PrivatePing/settings/.env
   echo "SECRET_ADMIN_URL=''" >> PrivatePing/settings/.env
   echo "HCAPTCHA_SITEKEY='10000000-ffff-ffff-ffff-000000000001'" >> PrivatePing/settings/.env
   echo "HCAPTCHA_SECRET='0x0000000000000000000000000000000000000000'" >> PrivatePing/settings/.env
9. **Run Database Migrations:** This command applies migrations to create necessary database tables.
   ```bash
   python3 manage.py migrate

10. **Start the Server:** This command starts the Django development server. You can access PrivatePing through your web browser at http://localhost:8000.
    ```bash
    python3 manage.py runserver


## Contributors

We extend our heartfelt gratitude to all contributors who have helped improve PrivatePing! Your efforts are greatly appreciated. See the [humans.txt](https://privateping.bytespot.tech/humans.txt) page for a list of contributors.

Contributions are welcome! If you'd like to contribute to PrivatePing, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and ensure the code follows the project's coding standards.
4. Submit a pull request with a clear description of your changes.

We invite everyone to use this absolutely free application and suggest improvements that can enhance security and privacy.

## License

PrivatePing is licensed under the [MIT License](LICENSE).

Special thanks to [@Madhur215](https://github.com/Madhur215/Django-ChatApp) for the groundwork and inspiration for this project.