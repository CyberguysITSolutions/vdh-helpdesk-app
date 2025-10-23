# 🎫 IT Help Desk System

A modern, cloud-native help desk application built with Streamlit and Azure SQL Database.

## Features

- 📊 **Dashboard** - Real-time ticket metrics and statistics
- 🎫 **Ticket Management** - View, filter, and manage support tickets
- 👥 **User Management** - Manage agents and customers
- 🔍 **Query Builder** - Run custom SQL queries for analytics
- ⚡ **Real-time Updates** - Connected directly to Azure SQL Database

## Tech Stack

- **Frontend**: Streamlit (Python)
- **Database**: Azure SQL Database
- **Deployment**: Streamlit Cloud / Azure App Service / Docker

## Quick Start

### Prerequisites

- Python 3.11+
- Azure SQL Database credentials
- Git (for deployment)

### Local Development

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd helpdesk-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml`:
   ```toml
   [database]
   server = "your-server.database.windows.net"
   database = "helpdesk-db"
   username = "your_username"
   password = "your_password"
   ```

4. Run the app:
   ```bash
   streamlit run helpdesk_app.py
   ```

5. Open your browser to `http://localhost:8501`

## Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions including:
- Streamlit Cloud (recommended)
- Azure App Service
- Docker containers
- Local development

## Database Schema

The app connects to Azure SQL with the following main tables:

**dbo.users**
- id, username, email, first_name, last_name, role, created_at, is_active, last_login

**dbo.Tickets**
- ticket_id, status, priority, name, email, location, phone_number, short_description, description, created_at, first_response_at, resolved_at, assigned_to

## Configuration

### Environment Variables

For non-Streamlit Cloud deployments, you can use environment variables:

```bash
export DB_SERVER="your-server.database.windows.net"
export DB_DATABASE="helpdesk-db"
export DB_USERNAME="your_username"
export DB_PASSWORD="your_password"
```

### Azure SQL Firewall

Make sure to add your deployment IP to Azure SQL firewall rules:

1. Go to Azure Portal
2. Navigate to your SQL Server
3. Settings → Networking
4. Add your client IP or allow Azure services

## Usage

### Dashboard
View key metrics including:
- Open tickets count
- In-progress tickets
- Urgent tickets
- Recent ticket activity

### Tickets Page
- Filter tickets by status and priority
- View detailed ticket information
- Track customer details and responses
- Monitor assignment and resolution times

### Users Page
- View all system users
- See user roles and activity
- Track last login information

### Query Builder
- Run custom SQL queries
- Use pre-built query templates
- Export results as CSV
- Analyze data in real-time

## Sample Queries

Check `azure_queries.sql` for a comprehensive collection of useful queries including:
- Dashboard statistics
- Ticket analytics
- User management
- Performance metrics

## Security

⚠️ **Important Security Notes:**

- Never commit database credentials to Git
- Use `.gitignore` to exclude secrets files
- Store credentials in Streamlit Cloud secrets or Azure Key Vault
- Enable Azure SQL firewall rules appropriately
- Use strong passwords and consider Managed Identity for Azure deployments

## Troubleshooting

### Connection Issues
- Verify database credentials
- Check Azure SQL firewall rules
- Ensure ODBC Driver 18 is installed (local/Docker only)

### Query Errors
- Verify table and column names match your schema
- Check `azure_queries.sql` for correct syntax
- Use INFORMATION_SCHEMA queries to inspect database structure

### Deployment Issues
- Check `requirements.txt` is included
- Verify secrets are configured correctly
- Review deployment platform logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this for your projects!

## Support

For issues or questions:
- Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Review the SQL queries in `azure_queries.sql`
- Open an issue on GitHub

## Roadmap

- [ ] Add user authentication
- [ ] Implement ticket response system
- [ ] Add email notifications
- [ ] Create mobile-responsive design
- [ ] Add file attachments for tickets
- [ ] Integrate with Teams/Slack
- [ ] Add reporting and analytics dashboard
- [ ] Implement SLA tracking

---

Built with ❤️ using Streamlit and Azure
