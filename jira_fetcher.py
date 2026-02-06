#!/usr/bin/env python3
"""
JIRA Ticket Fetcher
Fetches all tickets for a specific JIRA project using the JIRA REST API.
"""

import argparse
import sys
import json
from typing import List, Dict, Any
try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("Error: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)


class JiraFetcher:
    """Handles fetching tickets from JIRA using the REST API."""

    def __init__(self, jira_url: str, email: str, api_token: str):
        """
        Initialize the JIRA fetcher.

        Args:
            jira_url: Base URL of your JIRA instance (e.g., https://your-domain.atlassian.net)
            email: Your JIRA account email
            api_token: Your JIRA API token
        """
        self.jira_url = jira_url.rstrip('/')
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def fetch_all_tickets(self, project_key: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch all tickets for a given project.

        Args:
            project_key: The JIRA project key (e.g., 'PROJ')
            max_results: Number of results per page (max 100)

        Returns:
            List of ticket dictionaries
        """
        all_issues = []
        start_at = 0

        # JQL query to get all issues in the project
        jql = f"project = {project_key} ORDER BY created DESC"

        print(f"Fetching tickets for project: {project_key}")

        while True:
            url = f"{self.jira_url}/rest/api/2/search"
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,status,assignee,created,updated,priority,issuetype,reporter,description"
            }

            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    auth=self.auth,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                issues = data.get('issues', [])

                if not issues:
                    break

                all_issues.extend(issues)
                print(f"Fetched {len(all_issues)} tickets so far...")

                # Check if there are more results
                total = data.get('total', 0)
                if start_at + len(issues) >= total:
                    break

                start_at += len(issues)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching tickets: {e}")
                if hasattr(e.response, 'text'):
                    print(f"Response: {e.response.text}")
                sys.exit(1)

        print(f"\nTotal tickets fetched: {len(all_issues)}")
        return all_issues

    def transform_to_prd_format(self, tickets: List[Dict[str, Any]], project_name: str,
                                 branch_name: str = None, project_description: str = None) -> Dict[str, Any]:
        """
        Transform JIRA tickets to PRD format matching the userStories structure.

        Args:
            tickets: List of JIRA ticket dictionaries
            project_name: Name of the project
            branch_name: Optional branch name for the PRD
            project_description: Optional project description

        Returns:
            Dictionary in PRD format with userStories array
        """
        user_stories = []

        # Priority mapping: JIRA priority names to numeric priority
        priority_map = {
            'highest': 1,
            'high': 2,
            'medium': 3,
            'low': 4,
            'lowest': 5
        }

        for idx, ticket in enumerate(tickets, start=1):
            key = ticket.get('key', f'US-{idx:03d}')
            fields = ticket.get('fields', {})

            # Get basic fields
            title = fields.get('summary', 'Untitled')

            # Get description (handle different formats)
            description_obj = fields.get('description', {})
            if isinstance(description_obj, dict):
                # JIRA API v3 returns Atlassian Document Format (ADF)
                description = self._extract_text_from_adf(description_obj)
            else:
                description = description_obj if description_obj else f"Implement {title}"

            # Parse acceptance criteria from description
            acceptance_criteria = self._extract_acceptance_criteria(description)
            if not acceptance_criteria:
                acceptance_criteria = [
                    f"Implement {title}",
                    "Code passes all tests",
                    "Documentation updated"
                ]

            # Get priority
            priority_obj = fields.get('priority', {})
            priority_name = priority_obj.get('name', 'medium').lower() if priority_obj else 'medium'
            priority_num = priority_map.get(priority_name, idx)

            # Get status to determine if it passes
            status = fields.get('status', {}).get('name', '').lower()
            passes = status in ['done', 'closed', 'resolved', 'completed']

            user_story = {
                "id": key,
                "title": title,
                "description": description,
                "acceptanceCriteria": acceptance_criteria,
                "priority": priority_num,
                "passes": passes,
                "notes": ""
            }

            user_stories.append(user_story)

        # Create PRD structure
        prd = {
            "project": project_name,
            "branchName": branch_name or f"feature/{project_name.lower().replace(' ', '-')}",
            "description": project_description or f"JIRA tickets for project {project_name}",
            "userStories": user_stories
        }

        return prd

    def _extract_text_from_adf(self, adf_doc: Dict[str, Any]) -> str:
        """
        Extract plain text from Atlassian Document Format.

        Args:
            adf_doc: ADF document dictionary

        Returns:
            Plain text string
        """
        if not isinstance(adf_doc, dict):
            return str(adf_doc)

        text_parts = []

        def traverse(node):
            if isinstance(node, dict):
                # Handle text nodes
                if node.get('type') == 'text':
                    text_parts.append(node.get('text', ''))
                # Handle paragraph breaks
                elif node.get('type') in ['paragraph', 'heading']:
                    if text_parts and text_parts[-1] != '\n':
                        text_parts.append('\n')

                # Traverse children
                content = node.get('content', [])
                for child in content:
                    traverse(child)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(adf_doc)
        return ' '.join(text_parts).strip()

    def _extract_acceptance_criteria(self, description: str) -> List[str]:
        """
        Extract acceptance criteria from description text.

        Args:
            description: Ticket description text

        Returns:
            List of acceptance criteria strings
        """
        criteria = []
        lines = description.split('\n')
        in_criteria_section = False

        for line in lines:
            line = line.strip()
            # Look for acceptance criteria section
            if 'acceptance criteria' in line.lower() or 'acceptance' in line.lower():
                in_criteria_section = True
                continue

            # Stop if we hit another section
            if in_criteria_section and line and line[0].isupper() and ':' in line:
                break

            # Extract bullet points or numbered items
            if in_criteria_section and line:
                # Remove common bullet/number prefixes
                cleaned = line.lstrip('•-*→►▪▸ ')
                if cleaned and cleaned[0].isdigit():
                    cleaned = cleaned.lstrip('0123456789.)')
                cleaned = cleaned.strip()
                if cleaned:
                    criteria.append(cleaned)

        return criteria



def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fetch JIRA tickets and convert them to PRD format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url https://your-domain.atlassian.net --email user@example.com --token YOUR_API_TOKEN --project PROJ --output prd.json
  %(prog)s --url https://your-domain.atlassian.net --email user@example.com --token YOUR_API_TOKEN --project PROJ --project-name "MyApp" --output prd.json
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='JIRA instance URL (e.g., https://your-domain.atlassian.net)'
    )
    parser.add_argument(
        '--email',
        required=True,
        help='Your JIRA account email'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Your JIRA API token (create one at https://id.atlassian.com/manage-profile/security/api-tokens)'
    )
    parser.add_argument(
        '--project',
        required=True,
        help='JIRA project key (e.g., PROJ, DEV, etc.)'
    )
    parser.add_argument(
        '--project-name',
        help='Project name for PRD (defaults to project key)'
    )
    parser.add_argument(
        '--branch-name',
        help='Branch name for PRD (auto-generated if not provided)'
    )
    parser.add_argument(
        '--project-description',
        help='Project description for PRD'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output JSON file path (e.g., prd.json)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=100,
        help='Number of results per page (default: 100, max: 100)'
    )

    args = parser.parse_args()

    # Validate max_results
    if args.max_results < 1 or args.max_results > 100:
        print("Error: --max-results must be between 1 and 100")
        sys.exit(1)

    # Create fetcher instance
    fetcher = JiraFetcher(args.url, args.email, args.token)

    # Fetch tickets
    tickets = fetcher.fetch_all_tickets(args.project, args.max_results)

    # Transform to PRD format
    project_name = args.project_name or args.project
    prd_data = fetcher.transform_to_prd_format(
        tickets,
        project_name,
        args.branch_name,
        args.project_description
    )

    # Save PRD format to file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(prd_data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ PRD format saved to: {args.output}")
        print(f"   Project: {prd_data['project']}")
        print(f"   User Stories: {len(prd_data['userStories'])}")
    except IOError as e:
        print(f"Error saving to file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
