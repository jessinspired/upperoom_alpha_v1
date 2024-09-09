# Upperoom

**Version:** 1.0.0  
**Contributors:** [Jesse Obelem](https://github.com/jessinspired) | [Franklin Obasi](https://github.com/frankinobasy)


## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact Information](#contact-information)

## Overview

Upperoom is a web application designed to help students find suitable accommodation. The platform connects students seeking housing with creators who list available accommodations, ensuring a seamless and efficient process. By facilitating communication and transactions, Upperoom aims to enhance the accommodation search experience for students while providing creators with a valuable income opportunity.

## Features

- **User Registration:** Students and creators can easily register and create accounts.
- **Subscription Model:** Students can subscribe to specific locations and types of accommodation to receive notifications about new listings.
- **Automated Notifications:** Subscribers receive alerts when new listings are available, ensuring they never miss an opportunity.
- **Listing Management:** Creators can post and manage their accommodation listings, tracking the status of each listing.
- **Automated Status Updates:** Listings transition through various statuses (unverified, verified, probation, rejected, settled) based on user interactions and complaints.
- **Income for Creators:** Creators earn a percentage of the subscription fees when their listings are verified.
- **Robust Complaint Resolution:** A structured process for handling complaints, ensuring accountability and trust.

## Technology Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Deployment:** AWS
- **Version Control:** Git

## Installation

To get started with Upperoom, follow these steps:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/jessinspired/upperoom.git
   cd upperoom
   ```

2. **Set Up Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables:**
   Create a `.env` file in the root directory and configure your environment variables.

5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```

## Usage

Once the server is running, visit `http://127.0.0.1:8000` in your web browser. From there, you can register as a student or creator and begin using the platform.

## Project Structure

The project is organized into the following directories:

- **auths:** Handles authentication and user management.
- **core:** Contains the core functionalities of the application.
- **listings:** Manages accommodation listings and their statuses.
- **messaging:** Facilitates messaging and notifications between users.
- **payments:** Manages payment processing and subscription fees.
- **subscriptions:** Handles user subscriptions to listings.
- **templates:** Contains HTML templates for the application.
- **users:** Manages user-related functionalities for clients and creators.

## Contributing

We welcome contributions to Upperoom! If you'd like to contribute, please fork the repository and create a pull request. For any issues, please open an issue in the repository.

## License

This project is licensed under the [Your License] License. See the [LICENSE](LICENSE) file for more details.

## Contact Information

For any inquiries, please contact: Please contact the Authors
