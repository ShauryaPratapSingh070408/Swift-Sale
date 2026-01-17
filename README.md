# SwiftSale - Point of Sale System

SwiftSale is a comprehensive Point of Sale (POS) application developed using Python and the Kivy framework. Designed for efficiency and reliability, it integrates a robust MySQL database backend with a touch-optimized user interface. The system includes features for inventory management, real-time sales tracking, customer relationship management, and digital receipt generation via an embedded Flask server.

## Table of Contents

1.  [Project Overview](#project-overview)
2.  [Key Features](#key-features)
3.  [Technical Architecture](#technical-architecture)
4.  [Prerequisites](#prerequisites)
5.  [Installation](#installation)
6.  [Configuration](#configuration)
7.  [Usage](#usage)
8.  [License](#license)

## Project Overview

SwiftSale provides a standalone solution for retail environments. It bridges the gap between traditional desktop POS systems and modern mobile interfaces. By leveraging MySQL, it ensures data persistence and integrity suitable for high-volume transaction environments.

## Key Features

*   **Dashboard Analytics:** Provides real-time visualization of daily and monthly sales data, pending dues, and high-priority stock alerts.
*   **Transaction Processing:** Features a streamlined checkout interface supporting item lookup via autocomplete, quantity adjustments, and cart management.
*   **Inventory Management:** Allows administrators to add, update, and categorize products, with automatic stock deduction upon sale completion.
*   **Customer Directory:** Maintain a database of customer contact details and link specific customers to sales transactions.
*   **Split Payment & Discounts:** Supports percentage-based discounts and cash payment recording.
*   **Digital Receipts:** Integrated Flask server generates unique URLs and QR codes for every transaction, allowing customers to view receipts digitally without physical printing.

## Technical Architecture

*   **Frontend:** Kivy (Python NUI Framework) for cross-platform rendering.
*   **Backend Logic:** Python 3.
*   **Database:** MySQL Server accessed via `mysql-connector-python`.
*   **Microservice:** Flask (running in a daemon thread) for serving HTTP receipt views.
*   **Utilities:** QR Code generation for seamless mobile data transfer.

## Prerequisites

Ensure the following software is installed on the host machine before deployment:

*   **Python 3.8** or higher.
*   **MySQL Server** (Community Edition or equivalent).
*   **Git** (for version control).

## Installation

Follow these steps to set up the development environment:

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/ShauryaPratapSingh070408/Swift-Sale.git
    cd Swift-Sale
    ```

2.  **Create a Virtual Environment**
    It is recommended to run this application within an isolated environment.
    ```bash
    python -m venv venv
    
    # On Windows:
    venv\Scripts\activate
    
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    Install the necessary Python packages:
    ```bash
    pip install kivy mysql-connector-python flask qrcode[pil]
    ```

## Configuration

Before launching the application, you must configure the database connection settings to match your local MySQL instance.

1.  Open `main.py` in your preferred text editor.
2.  Locate the `DB_CONFIG` dictionary near the top of the file.
3.  Update the credentials:

    ```python
    DB_CONFIG = {
        'host': 'localhost',      # Hostname (usually localhost)
        'user': 'root',           # Your MySQL username
        'password': 'your_password', # Your MySQL password
        'database': 'SwiftSale_DB'   # The application will create this automatically
    }
    ```

4.  Ensure your MySQL server service is running.

## Usage

### Starting the Application

Execute the main script from the command line:

```bash
python main.py
```

### Authentication

Upon the first run, the system initializes the database and creates a default administrator account.

*   **Username:** admin
*   **Password:** 132009

### Operational Workflow

1.  **Dashboard:** Upon login, view key performance indicators.
2.  **Inventory:** Navigate to the Inventory screen to populate the database with products.
3.  **POS:** Use the "New Sale" section to process transactions.
    *   Search for products or customers.
    *   Add items to the cart.
    *   Select "Charge" to finalize.
4.  **Receipts:** A QR code will be displayed upon successful payment. Scanning this code connects to the local Flask server (port 8000) to display the HTML receipt.

## License

This project is open-source and available under the MIT License. 
