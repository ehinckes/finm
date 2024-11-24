# FinM - Financial Portfolio Management System

## Overview
FinM Tracker is a comprehensive financial portfolio management system built with Django. It enables users to track their investment portfolio, analyze performance, assess risks, and make data-driven investment decisions. This project is still under development and is NOT meant to be used for real investment decisions.

## Features
- **Portfolio Management**
  - Track multiple investment assets
  - Record and manage transactions
  - (Near) live data for assets
  - Analysis of asset allocation

- **User Management**
  - Secure user authentication
  - Personalized portfolio tracking
  - Custom user profiles

- **Data Integration**
  - External API integration for real-time market data
  - Custom web scraping capabilities
  - Automated data updates
  - Live data cached for 15 minutes

- **Next To Be Added**
  - Generate financial projections
  - Risk assessment tools

## Tech Stack
- **Backend**: Django
- **Database**: PostgreSQL
- **Frontend**: 
  - HTML templates with Django templating engine
  - TailwindCSS for styling
- **Additional Tools**:
  - Custom templating filters
  - API integrations
  - Testing suite

## Project Structure
```
finm_tracker/
├── portfolio/                 # Main application
│   ├── services/             # Business logic and external services
│   ├── templates/            # Frontend templates
│   ├── templatetags/         # Custom template filters
│   └── tests/                # Test suite
├── users/                    # User management app
├── theme/                    # Frontend styling with TailwindCSS
└── requirements.txt          # Project dependencies
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ehinckes/finm.git
cd finm_tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Set up TailwindCSS:
```bash
cd theme/static_src
npm install
npm run build
```

6. Start the development server:
```bash
python manage.py runserver
```

## Testing
Run the test suite:
```bash
python manage.py test
```

Tests cover:
- Models
- Serializers
- Services
- Views

## License

MIT License

Copyright (c) 2024 Elliott Hinckesman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contact

GitHub: @ehinckes
