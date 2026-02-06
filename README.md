# JIRA Ticket Fetcher

A Python tool that fetches all JIRA tickets for a specific project and converts them into a structured PRD (Product Requirements Document) format with user stories.  
Used for the Ralph tool located here https://github.com/snarktank/ralph

## Features

- Fetches all tickets from a JIRA project using the JIRA REST API
- Supports pagination to handle large numbers of tickets
- Converts JIRA tickets to PRD format with user stories
- Extracts acceptance criteria from ticket descriptions
- Maps JIRA priorities to numeric priorities
- Determines ticket completion status (passes/fails)
- Handles Atlassian Document Format (ADF) descriptions
- Exports data to JSON format

## Prerequisites

- Python 3.6 or higher
- JIRA account with API access
- JIRA API token

## Installation

1. Clone or download this repository:
```bash
git clone <repository-url>
cd ralph_jira
```

2. Install required dependencies:
```bash
pip install requests
```

## Getting a JIRA API Token

1. Log in to your Atlassian account
2. Go to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
3. Click "Create API token"
4. Give it a label (e.g., "JIRA Fetcher")
5. Copy the generated token (you won't be able to see it again!)

## Usage

### Basic Usage

```bash
python jira_fetcher.py \
  --url https://your-domain.atlassian.net \
  --email your-email@example.com \
  --token YOUR_API_TOKEN \
  --project PROJ \
  --output prd.json
```

### Advanced Usage with Custom Options

```bash
python jira_fetcher.py \
  --url https://your-domain.atlassian.net \
  --email your-email@example.com \
  --token YOUR_API_TOKEN \
  --project PROJ \
  --project-name "My Awesome Project" \
  --branch-name "feature/my-project" \
  --project-description "Description of my project" \
  --output data/prd.json \
  --max-results 50
```

### Command-Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--url` | Yes | JIRA instance URL (e.g., https://your-domain.atlassian.net) |
| `--email` | Yes | Your JIRA account email |
| `--token` | Yes | Your JIRA API token |
| `--project` | Yes | JIRA project key (e.g., PROJ, DEV) |
| `--output` | Yes | Output JSON file path (e.g., prd.json) |
| `--project-name` | No | Project name for PRD (defaults to project key) |
| `--branch-name` | No | Branch name for PRD (auto-generated if not provided) |
| `--project-description` | No | Project description for PRD |
| `--max-results` | No | Number of results per page (default: 100, max: 100) |

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "project": "Project Name",
  "branchName": "feature/project-name",
  "description": "Project description",
  "userStories": [
    {
      "id": "PROJ-123",
      "title": "Ticket summary",
      "description": "Detailed description",
      "acceptanceCriteria": [
        "Criterion 1",
        "Criterion 2",
        "Criterion 3"
      ],
      "priority": 2,
      "passes": false,
      "notes": ""
    }
  ]
}
```

### Field Descriptions

- **project**: Name of the project
- **branchName**: Git branch name for the feature
- **description**: Project description
- **userStories**: Array of user story objects
  - **id**: JIRA ticket key (e.g., PROJ-123)
  - **title**: Ticket summary
  - **description**: Ticket description (extracted from ADF or plain text)
  - **acceptanceCriteria**: List of acceptance criteria extracted from description
  - **priority**: Numeric priority (1=highest, 5=lowest)
  - **passes**: Boolean indicating if ticket is completed (true for Done/Closed/Resolved/Completed status)
  - **notes**: Additional notes (empty by default)

## Priority Mapping

JIRA priorities are mapped to numeric values:

| JIRA Priority | Numeric Value |
|---------------|---------------|
| Highest | 1 |
| High | 2 |
| Medium | 3 |
| Low | 4 |
| Lowest | 5 |

## Acceptance Criteria Extraction

The tool automatically extracts acceptance criteria from ticket descriptions by:
1. Looking for "Acceptance Criteria" or "Acceptance" section headers
2. Extracting bullet points or numbered items below the header
3. If no criteria are found, generates default criteria based on the ticket title

## Examples

### Example 1: Fetch tickets for a project

```bash
python jira_fetcher.py \
  --url https://mycompany.atlassian.net \
  --email john@mycompany.com \
  --token abcd1234efgh5678 \
  --project WEB \
  --output web-project-prd.json
```

### Example 2: Fetch with custom project details

```bash
python jira_fetcher.py \
  --url https://mycompany.atlassian.net \
  --email john@mycompany.com \
  --token abcd1234efgh5678 \
  --project API \
  --project-name "REST API v2" \
  --branch-name "feature/api-v2" \
  --project-description "New REST API endpoints for v2" \
  --output data/api-v2-prd.json
```

## Project Structure

```
ralph_jira/
├── jira_fetcher.py    # Main script
├── data/              # Output directory for generated JSON files
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Troubleshooting

### Authentication Errors
- Verify your email and API token are correct
- Ensure your API token hasn't expired
- Check that you have access to the specified JIRA project

### No Tickets Found
- Verify the project key is correct (case-sensitive)
- Ensure the project exists and you have permission to view it
- Check that the project contains tickets

### Rate Limiting
- If you hit rate limits, reduce the `--max-results` value
- Add delays between requests by modifying the script if needed

## Security Notes

- Never commit your API token to version control
- Store credentials securely (use environment variables or a secrets manager)
- The `.gitignore` file is configured to exclude sensitive data files

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open source and available under the MIT License.
