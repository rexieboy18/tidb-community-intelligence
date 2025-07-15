import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
from collections import Counter
import time

class TiDBDataCollector:
    def __init__(self, github_token=None):
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'TiDB-Community-Intelligence'
        }
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def collect_issues(self, repo="pingcap/tidb", max_issues=200):
        """Collect TiDB issues from GitHub API"""
        print(f"🔍 Collecting issues from {repo}...")
        
        issues = []
        page = 1
        per_page = 100
        
        while len(issues) < max_issues:
            url = f"{self.base_url}/repos/{repo}/issues"
            params = {
                'state': 'all',
                'per_page': min(per_page, max_issues - len(issues)),
                'page': page,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                batch = response.json()
                if not batch:
                    break
                
                # Filter out pull requests
                filtered_batch = [issue for issue in batch if 'pull_request' not in issue]
                issues.extend(filtered_batch)
                
                print(f"   Collected {len(issues)} issues...")
                
                # Respect rate limits
                time.sleep(0.5)
                page += 1
                
                if len(batch) < per_page:  # Last page
                    break
                
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Error collecting issues: {e}")
                break
        
        print(f"✅ Total collected: {len(issues)} issues")
        return issues[:max_issues]
    
    def categorize_issue(self, issue):
        """Categorize issue based on labels and title"""
        labels = [label['name'].lower() for label in issue['labels']]
        title = issue['title'].lower()
        body = (issue['body'] or '').lower()
        
        # Priority order: check labels first, then title keywords
        if any('bug' in label for label in labels):
            return 'bug'
        elif any(label in ['enhancement', 'feature', 'type/enhancement'] for label in labels):
            return 'enhancement'
        elif any('question' in label for label in labels):
            return 'question'
        elif any('help' in label for label in labels):
            return 'help'
        elif any(word in title for word in ['performance', 'slow', 'optimization', 'latency']):
            return 'performance'
        elif any(word in title for word in ['configuration', 'config', 'setup', 'install']):
            return 'configuration'
        elif any(word in title for word in ['migration', 'migrate', 'import']):
            return 'migration'
        elif any(word in title for word in ['error', 'fail', 'panic', 'crash']):
            return 'error'
        elif any(word in title for word in ['documentation', 'doc', 'readme']):
            return 'documentation'
        else:
            return 'other'
    
    def extract_tech_context(self, issue):
        """Extract technical context from issue"""
        text = (issue['title'] + ' ' + (issue['body'] or '')).lower()
        
        tech_patterns = {
            'kubernetes': ['kubernetes', 'k8s', 'kubectl', 'pod', 'namespace', 'helm'],
            'docker': ['docker', 'container', 'dockerfile', 'image'],
            'mysql': ['mysql', 'mariadb', 'migration', 'compatibility'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 's3', 'ec2'],
            'monitoring': ['prometheus', 'grafana', 'monitoring', 'metrics', 'alerting'],
            'backup': ['backup', 'restore', 'br', 'dumpling'],
            'replication': ['replication', 'replica', 'sync', 'binlog'],
            'performance': ['slow', 'performance', 'optimization', 'latency', 'bottleneck'],
            'tiflash': ['tiflash', 'columnar', 'analytical'],
            'tikv': ['tikv', 'storage', 'raftstore'],
            'pd': ['pd', 'placement driver', 'scheduler'],
            'cdc': ['cdc', 'change data capture', 'ticdc']
        }
        
        found_tech = []
        for tech, keywords in tech_patterns.items():
            if any(keyword in text for keyword in keywords):
                found_tech.append(tech)
        
        return found_tech
    
    def extract_error_patterns(self, issue):
        """Extract error messages and patterns"""
        text = (issue['title'] + ' ' + (issue['body'] or '')).lower()
        
        error_patterns = []
        
        # Common error indicators
        error_keywords = [
            'error:', 'failed:', 'panic:', 'exception:', 'timeout:',
            'connection refused', 'out of memory', 'deadlock',
            'cannot connect', 'permission denied', 'not found'
        ]
        
        for keyword in error_keywords:
            if keyword in text:
                error_patterns.append(keyword)
        
        return error_patterns
    
    def process_issues(self, issues):
        """Process raw issues into structured format"""
        processed_issues = []
        
        print("🔄 Processing issues...")
        
        for i, issue in enumerate(issues):
            processed_issue = {
                'id': issue['id'],
                'number': issue['number'],
                'title': issue['title'],
                'body': issue['body'] or '',
                'state': issue['state'],
                'created_at': issue['created_at'],
                'updated_at': issue['updated_at'],
                'closed_at': issue['closed_at'],
                'labels': [label['name'] for label in issue['labels']],
                'comments_count': issue['comments'],
                'author': issue['user']['login'],
                'assignees': [assignee['login'] for assignee in issue.get('assignees', [])],
                'milestone': issue['milestone']['title'] if issue.get('milestone') else None,
                
                # Derived fields
                'category': self.categorize_issue(issue),
                'tech_context': self.extract_tech_context(issue),
                'error_patterns': self.extract_error_patterns(issue),
                'has_solution': issue['state'] == 'closed' and issue['comments'] > 0,
                'is_recent': self.is_recent_issue(issue['created_at']),
                'engagement_score': self.calculate_engagement_score(issue)
            }
            
            processed_issues.append(processed_issue)
            
            if (i + 1) % 50 == 0:
                print(f"   Processed {i + 1} issues...")
        
        print(f"✅ Processed {len(processed_issues)} issues")
        return processed_issues
    
    def is_recent_issue(self, created_at):
        """Check if issue was created in the last 90 days"""
        from datetime import datetime, timedelta
        
        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        recent_threshold = datetime.now().replace(tzinfo=created_date.tzinfo) - timedelta(days=90)
        
        return created_date > recent_threshold
    
    def calculate_engagement_score(self, issue):
        """Calculate engagement score based on comments, labels, etc."""
        score = 0
        
        # Base score from comments
        score += min(issue['comments'] * 2, 20)  # Cap at 20
        
        # Bonus for labels
        score += len(issue['labels'])
        
        # Bonus for assignees
        score += len(issue.get('assignees', [])) * 3
        
        # Bonus for milestone
        if issue.get('milestone'):
            score += 5
        
        return min(score, 50)  # Cap at 50
    
    def generate_analytics(self, processed_issues):
        """Generate comprehensive analytics"""
        print("📊 Generating analytics...")
        
        df = pd.DataFrame(processed_issues)
        
        analytics = {
            'summary': {
                'total_issues': len(processed_issues),
                'open_issues': len(df[df['state'] == 'open']),
                'closed_issues': len(df[df['state'] == 'closed']),
                'solution_rate': len(df[df['has_solution']]) / len(df) if len(df) > 0 else 0,
                'recent_issues': len(df[df['is_recent']]),
                'avg_comments': df['comments_count'].mean(),
                'avg_engagement': df['engagement_score'].mean()
            },
            
            'categories': {
                'distribution': df['category'].value_counts().to_dict(),
                'solution_rates': df.groupby('category')['has_solution'].mean().to_dict(),
                'avg_engagement': df.groupby('category')['engagement_score'].mean().to_dict()
            },
            
            'technology': {
                'usage': self.analyze_tech_usage(processed_issues),
                'combinations': self.analyze_tech_combinations(processed_issues)
            },
            
            'temporal': {
                'monthly_trends': self.analyze_monthly_trends(df),
                'resolution_times': self.analyze_resolution_times(df)
            },
            
            'community': {
                'top_contributors': df['author'].value_counts().head(10).to_dict(),
                'engagement_distribution': df['engagement_score'].describe().to_dict()
            }
        }
        
        return analytics
    
    def analyze_tech_usage(self, issues):
        """Analyze technology usage patterns"""
        tech_counter = Counter()
        
        for issue in issues:
            for tech in issue['tech_context']:
                tech_counter[tech] += 1
        
        return dict(tech_counter.most_common(15))
    
    def analyze_tech_combinations(self, issues):
        """Analyze common technology combinations"""
        combinations = Counter()
        
        for issue in issues:
            tech_context = issue['tech_context']
            if len(tech_context) > 1:
                # Create combinations of technologies
                from itertools import combinations as itertools_combinations
                for combo in itertools_combinations(sorted(tech_context), 2):
                    combinations[combo] += 1
        
        return [{'technologies': list(combo), 'count': count} 
                for combo, count in combinations.most_common(10)]
    
    def analyze_monthly_trends(self, df):
        """Analyze monthly issue trends"""
        if df.empty:
            return {}
        
        df['created_month'] = pd.to_datetime(df['created_at']).dt.to_period('M')
        monthly_counts = df['created_month'].value_counts().sort_index()
        
        return {str(month): count for month, count in monthly_counts.items()}
    
    def analyze_resolution_times(self, df):
        """Analyze issue resolution times"""
        closed_issues = df[df['state'] == 'closed'].copy()
        
        if closed_issues.empty:
            return {}
        
        closed_issues['created'] = pd.to_datetime(closed_issues['created_at'])
        closed_issues['closed'] = pd.to_datetime(closed_issues['closed_at'])
        closed_issues['resolution_hours'] = (
            closed_issues['closed'] - closed_issues['created']
        ).dt.total_seconds() / 3600
        
        return {
            'avg_hours': closed_issues['resolution_hours'].mean(),
            'median_hours': closed_issues['resolution_hours'].median(),
            'by_category': closed_issues.groupby('category')['resolution_hours'].mean().to_dict()
        }
    
    def save_data(self, processed_issues, analytics):
        """Save all data to files"""
        os.makedirs('data', exist_ok=True)
        
        # Save processed issues
        with open('data/tidb_issues.json', 'w') as f:
            json.dump(processed_issues, f, indent=2, default=str)
        
        # Save analytics
        with open('data/analytics.json', 'w') as f:
            json.dump(analytics, f, indent=2, default=str)
        
        # Save CSV for easy analysis
        df = pd.DataFrame(processed_issues)
        df.to_csv('data/tidb_issues.csv', index=False)
        
        print("💾 Data saved to:")
        print("   - data/tidb_issues.json")
        print("   - data/analytics.json")
        print("   - data/tidb_issues.csv")

def main():
    print("🤖 TiDB Community Intelligence - Advanced Data Collector")
    print("=" * 60)
    
    # Initialize collector
    collector = TiDBDataCollector()
    
    # Collect issues
    raw_issues = collector.collect_issues(max_issues=150)
    
    if not raw_issues:
        print("❌ No issues collected. Check your internet connection.")
        return
    
    # Process issues
    processed_issues = collector.process_issues(raw_issues)
    
    # Generate analytics
    analytics = collector.generate_analytics(processed_issues)
    
    # Save everything
    collector.save_data(processed_issues, analytics)
    
    # Print summary
    print("\n🎉 Collection Complete!")
    print(f"📊 Total Issues: {analytics['summary']['total_issues']}")
    print(f"✅ Solution Rate: {analytics['summary']['solution_rate']:.1%}")
    print(f"📈 Categories: {len(analytics['categories']['distribution'])}")
    print(f"🔧 Technologies: {len(analytics['technology']['usage'])}")
    
    print(f"\n🏆 Top Categories:")
    for category, count in list(analytics['categories']['distribution'].items())[:5]:
        print(f"   • {category}: {count}")
    
    print(f"\n🔧 Top Technologies:")
    for tech, count in list(analytics['technology']['usage'].items())[:5]:
        print(f"   • {tech}: {count}")
    
    print("\n🚀 Next step: Run the advanced demo!")
    print("   cd demo")
    print("   streamlit run advanced_app.py")

if __name__ == "__main__":
    main()