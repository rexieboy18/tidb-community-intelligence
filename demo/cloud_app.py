import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="TiDB Community Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def collect_live_data():
    """Collect live data from TiDB GitHub for demo"""
    try:
        url = "https://api.github.com/repos/pingcap/tidb/issues"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'TiDB-Community-Intelligence'
        }
        params = {
            'state': 'all',
            'per_page': 50,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        issues = response.json()
        
        # Filter out pull requests
        issues = [issue for issue in issues if 'pull_request' not in issue]
        
        # Process issues
        processed_issues = []
        for issue in issues:
            processed_issue = {
                'id': issue['id'],
                'title': issue['title'],
                'body': issue['body'] or '',
                'state': issue['state'],
                'labels': [label['name'] for label in issue['labels']],
                'comments': issue['comments'],
                'created_at': issue['created_at'],
                'is_solved': issue['state'] == 'closed' and issue['comments'] > 0,
                'category': categorize_issue(issue),
                'tech_context': extract_tech_context(issue)
            }
            processed_issues.append(processed_issue)
        
        return processed_issues
        
    except Exception as e:
        st.error(f"Could not fetch live data: {e}")
        return get_sample_data()

def categorize_issue(issue):
    """Categorize issue based on labels and title"""
    labels = [label['name'].lower() for label in issue['labels']]
    title = issue['title'].lower()
    
    if any('bug' in label for label in labels) or 'bug' in title:
        return 'bug'
    elif any(word in title for word in ['performance', 'slow', 'optimization']):
        return 'performance'
    elif any('question' in label for label in labels):
        return 'question'
    elif any('enhancement' in label for label in labels):
        return 'enhancement'
    else:
        return 'other'

def extract_tech_context(issue):
    """Extract technology context from issue"""
    text = (issue['title'] + ' ' + (issue['body'] or '')).lower()
    
    tech_keywords = {
        'kubernetes': ['kubernetes', 'k8s', 'kubectl'],
        'docker': ['docker', 'container', 'dockerfile'],
        'mysql': ['mysql', 'mariadb', 'migration'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud'],
        'monitoring': ['prometheus', 'grafana', 'monitoring'],
        'performance': ['slow', 'performance', 'optimization', 'latency']
    }
    
    found_tech = []
    for tech, keywords in tech_keywords.items():
        if any(keyword in text for keyword in keywords):
            found_tech.append(tech)
    
    return found_tech

def get_sample_data():
    """Fallback sample data if live API fails"""
    return [
        {
            'id': 1,
            'title': 'TiDB connection timeout in Kubernetes cluster',
            'body': 'Getting connection timeouts when running TiDB in k8s environment with high load',
            'state': 'closed',
            'labels': ['type/bug', 'area/tikv', 'severity/major'],
            'comments': 12,
            'created_at': '2024-01-15T10:00:00Z',
            'is_solved': True,
            'category': 'bug',
            'tech_context': ['kubernetes', 'performance']
        },
        {
            'id': 2,
            'title': 'Slow query performance with large dataset',
            'body': 'Queries taking too long on tables with millions of rows, need optimization tips',
            'state': 'open',
            'labels': ['type/question', 'area/sql', 'area/planner'],
            'comments': 8,
            'created_at': '2024-01-14T15:30:00Z',
            'is_solved': False,
            'category': 'performance',
            'tech_context': ['performance', 'mysql']
        },
        {
            'id': 3,
            'title': 'Docker deployment configuration help',
            'body': 'Need help configuring TiDB cluster in Docker environment for production',
            'state': 'closed',
            'labels': ['type/question', 'area/deployment'],
            'comments': 15,
            'created_at': '2024-01-13T09:20:00Z',
            'is_solved': True,
            'category': 'question',
            'tech_context': ['docker', 'cloud']
        },
        {
            'id': 4,
            'title': 'Migration from MySQL to TiDB best practices',
            'body': 'Looking for guidance on migrating large MySQL database to TiDB',
            'state': 'closed',
            'labels': ['type/question', 'area/migration'],
            'comments': 20,
            'created_at': '2024-01-12T14:45:00Z',
            'is_solved': True,
            'category': 'migration',
            'tech_context': ['mysql', 'cloud']
        },
        {
            'id': 5,
            'title': 'TiFlash replica sync issue',
            'body': 'TiFlash replicas not syncing properly with TiKV in our cluster',
            'state': 'open',
            'labels': ['type/bug', 'area/tiflash'],
            'comments': 6,
            'created_at': '2024-01-11T11:30:00Z',
            'is_solved': False,
            'category': 'bug',
            'tech_context': ['tiflash', 'performance']
        },
        {
            'id': 6,
            'title': 'Prometheus monitoring setup for TiDB',
            'body': 'How to properly configure Prometheus monitoring for TiDB cluster',
            'state': 'closed',
            'labels': ['type/question', 'area/monitoring'],
            'comments': 10,
            'created_at': '2024-01-10T16:20:00Z',
            'is_solved': True,
            'category': 'monitoring',
            'tech_context': ['monitoring', 'kubernetes']
        },
        {
            'id': 7,
            'title': 'AWS EKS deployment optimization',
            'body': 'Optimizing TiDB deployment on AWS EKS for better performance',
            'state': 'open',
            'labels': ['type/enhancement', 'area/deployment'],
            'comments': 4,
            'created_at': '2024-01-09T13:15:00Z',
            'is_solved': False,
            'category': 'enhancement',
            'tech_context': ['cloud', 'kubernetes', 'performance']
        },
        {
            'id': 8,
            'title': 'Backup and restore with BR tool',
            'body': 'Questions about using BR tool for backup and restore operations',
            'state': 'closed',
            'labels': ['type/question', 'area/br'],
            'comments': 7,
            'created_at': '2024-01-08T10:00:00Z',
            'is_solved': True,
            'category': 'question',
            'tech_context': ['backup', 'cloud']
        }
    ]

def find_similar_issues(query, issues, max_results=5):
    """Simple similarity matching"""
    if not query.strip():
        return []
    
    query_words = set(query.lower().split())
    similar_issues = []
    
    for issue in issues:
        title_words = set(issue['title'].lower().split())
        body_words = set((issue['body'] or '').lower().split())
        
        title_overlap = len(query_words.intersection(title_words))
        body_overlap = len(query_words.intersection(body_words))
        
        if title_overlap > 0 or body_overlap > 0:
            similarity_score = (title_overlap * 2 + body_overlap) / len(query_words)
            similar_issues.append({
                'issue': issue,
                'similarity': min(similarity_score, 1.0)
            })
    
    similar_issues.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_issues[:max_results]

def get_tech_recommendations(selected_tech, issues):
    """Generate tech stack recommendations"""
    recommendations = []
    
    for tech in selected_tech:
        tech_issues = [
            issue for issue in issues 
            if tech.lower() in [t.lower() for t in issue.get('tech_context', [])]
        ]
        
        if tech_issues:
            total_issues = len(tech_issues)
            solved_issues = sum(1 for issue in tech_issues if issue['is_solved'])
            solution_rate = solved_issues / total_issues if total_issues > 0 else 0
            
            categories = Counter(issue['category'] for issue in tech_issues)
            avg_comments = sum(issue['comments'] for issue in tech_issues) / total_issues
            
            recommendations.append({
                'technology': tech,
                'total_issues': total_issues,
                'solution_rate': solution_rate,
                'common_categories': dict(categories.most_common(3)),
                'avg_engagement': avg_comments,
                'sample_issues': tech_issues[:3]
            })
    
    return recommendations

def main():
    # Header
    st.title("🤖 TiDB Community Intelligence Platform")
    st.markdown("*Live demo powered by real TiDB GitHub data*")
    
    # Data loading with progress
    data_source = st.sidebar.radio(
        "📊 Data Source:",
        ["Live GitHub API", "Rich Sample Data"],
        help="Live API may have limited data. Sample data shows full functionality."
    )
    
    with st.spinner("🔄 Loading TiDB community data..."):
        if data_source == "Live GitHub API":
            issues = collect_live_data()
        else:
            issues = get_sample_data()
            st.info("📊 Using rich sample data to demonstrate full functionality")
    
    if not issues:
        st.error("Could not load data. Please try again later.")
        st.stop()
    
    st.success(f"✅ Loaded {len(issues)} recent TiDB issues from GitHub")
    
    # Debug info (remove this after fixing)
    with st.expander("🔍 Debug Info (Click to expand)"):
        st.write("**Sample issue structure:**")
        if issues:
            st.json(issues[0])
        
        categories = Counter(issue['category'] for issue in issues)
        st.write("**Categories found:**", dict(categories))
        
        tech_usage = Counter()
        for issue in issues:
            for tech in issue.get('tech_context', []):
                tech_usage[tech] += 1
        st.write("**Tech contexts found:**", dict(tech_usage))
    
    # Sidebar
    st.sidebar.header("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a feature:",
        ["🏠 Overview", "🔍 AI Issue Search", "🛠️ Tech Stack Intelligence", "📊 Community Insights"]
    )
    
    if page == "🏠 Overview":
        st.header("📊 Community Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Issues", len(issues))
        
        with col2:
            solved_count = sum(1 for issue in issues if issue['is_solved'])
            st.metric("Solution Rate", f"{solved_count/len(issues)*100:.1f}%")
        
        with col3:
            categories = set(issue['category'] for issue in issues)
            st.metric("Categories", len(categories))
        
        with col4:
            avg_comments = sum(issue['comments'] for issue in issues) / len(issues)
            st.metric("Avg Comments", f"{avg_comments:.1f}")
        
        # Category distribution
        st.subheader("Issue Categories")
        category_counts = Counter(issue['category'] for issue in issues)
        
        if category_counts and len(category_counts) > 0:
            # Create pie chart
            fig = px.pie(
                values=list(category_counts.values()),
                names=list(category_counts.keys()),
                title="Distribution of Issue Categories",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
            # Also show as bar chart for better readability
            fig_bar = px.bar(
                x=list(category_counts.keys()),
                y=list(category_counts.values()),
                title="Issue Count by Category",
                labels={'x': 'Category', 'y': 'Number of Issues'},
                color=list(category_counts.values()),
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No category data available for charts")
        
        # Technology usage chart
        st.subheader("🔧 Technology Mentions")
        tech_usage = Counter()
        for issue in issues:
            for tech in issue.get('tech_context', []):
                tech_usage[tech] += 1
        
        if tech_usage and len(tech_usage) > 0:
            fig_tech = px.bar(
                x=list(tech_usage.values()),
                y=list(tech_usage.keys()),
                orientation='h',
                title="Technologies Mentioned in Issues",
                labels={'x': 'Number of Mentions', 'y': 'Technology'},
                color=list(tech_usage.values()),
                color_continuous_scale='plasma'
            )
            st.plotly_chart(fig_tech, use_container_width=True)
        else:
            st.info("No technology context data available")
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        if len(issues) > 1:
            try:
                df = pd.DataFrame(issues)
                df['created_date'] = pd.to_datetime(df['created_at']).dt.date
                
                daily_issues = df.groupby('created_date').size().reset_index(name='count')
                
                if len(daily_issues) > 1:
                    fig_trend = px.line(
                        daily_issues, 
                        x='created_date', 
                        y='count', 
                        title="Daily Issue Creation Trend",
                        markers=True
                    )
                    fig_trend.update_layout(xaxis_title="Date", yaxis_title="Number of Issues")
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("Not enough data points for trend analysis")
            except Exception as e:
                st.warning(f"Could not generate trend chart: {e}")
        else:
            st.info("Need more data for trend analysis")
    
    elif page == "🔍 AI Issue Search":
        st.header("🔍 AI-Powered Issue Search")
        st.markdown("*Find similar issues from the TiDB community*")
        
        # Search input
        query = st.text_area(
            "Describe your TiDB issue:",
            placeholder="e.g., TiDB connection timeout in Kubernetes cluster",
            height=100
        )
        
        if query:
            with st.spinner("🔍 Searching for similar issues..."):
                similar_issues = find_similar_issues(query, issues)
            
            if similar_issues:
                st.subheader(f"Found {len(similar_issues)} Similar Issues:")
                
                for i, result in enumerate(similar_issues):
                    issue = result['issue']
                    similarity = result['similarity']
                    
                    with st.expander(f"#{i+1}: {issue['title']} (Similarity: {similarity:.1%})", expanded=(i==0)):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Category:** {issue['category']}")
                            st.write(f"**Status:** {'✅ Solved' if issue['is_solved'] else '🔄 Open'}")
                            st.write(f"**Comments:** {issue['comments']}")
                            
                            if issue['tech_context']:
                                st.write(f"**Technologies:** {', '.join(issue['tech_context'])}")
                            
                            if issue['body']:
                                st.write("**Description:**")
                                st.write(issue['body'][:300] + "..." if len(issue['body']) > 300 else issue['body'])
                        
                        with col2:
                            if issue['labels']:
                                st.write("**Labels:**")
                                for label in issue['labels'][:5]:
                                    st.code(label)
            else:
                st.info("💡 No similar issues found. Try different keywords.")
    
    elif page == "🛠️ Tech Stack Intelligence":
        st.header("🛠️ Tech Stack Intelligence")
        st.markdown("*Get insights based on your technology stack*")
        
        # Tech stack selection
        available_tech = ['Kubernetes', 'Docker', 'MySQL', 'Cloud', 'Monitoring', 'Performance']
        selected_tech = st.multiselect(
            "Select your technology stack:",
            available_tech,
            default=['Kubernetes', 'Docker']
        )
        
        if selected_tech:
            recommendations = get_tech_recommendations(selected_tech, issues)
            
            if recommendations:
                for rec in recommendations:
                    st.subheader(f"🔧 {rec['technology']} Analysis")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Issues Found", rec['total_issues'])
                    
                    with col2:
                        st.metric("Solution Rate", f"{rec['solution_rate']:.1%}")
                    
                    with col3:
                        st.metric("Avg Engagement", f"{rec['avg_engagement']:.1f}")
                    
                    if rec['common_categories']:
                        st.write("**Common Issue Types:**")
                        for category, count in rec['common_categories'].items():
                            st.write(f"• {category}: {count} issues")
                    
                    if rec['sample_issues']:
                        with st.expander("Sample Issues"):
                            for issue in rec['sample_issues']:
                                status = "✅" if issue['is_solved'] else "🔄"
                                st.write(f"{status} {issue['title']}")
                    
                    st.divider()
            else:
                st.info("🔍 No specific patterns found for your tech stack.")
    
    elif page == "📊 Community Insights":
        st.header("📊 Community Insights")
        
        # Technology usage
        st.subheader("🔧 Technology Landscape")
        tech_usage = Counter()
        for issue in issues:
            for tech in issue.get('tech_context', []):
                tech_usage[tech] += 1
        
        if tech_usage and len(tech_usage) > 0:
            fig = px.bar(
                x=list(tech_usage.values()),
                y=list(tech_usage.keys()),
                orientation='h',
                title="Technologies Mentioned in Issues",
                labels={'x': 'Number of Mentions', 'y': 'Technology'},
                color=list(tech_usage.values()),
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No technology mentions found in current dataset")
        
        # Solution effectiveness
        st.subheader("💡 Solution Effectiveness")
        categories = Counter(issue['category'] for issue in issues)
        
        if categories and len(categories) > 0:
            solution_rates = {}
            for category in categories.keys():
                cat_issues = [i for i in issues if i['category'] == category]
                if cat_issues:
                    solved = sum(1 for i in cat_issues if i['is_solved'])
                    solution_rates[category] = solved / len(cat_issues)
            
            if solution_rates:
                fig = px.bar(
                    x=list(solution_rates.keys()),
                    y=[rate * 100 for rate in solution_rates.values()],
                    title="Solution Rate by Category (%)",
                    labels={'x': 'Category', 'y': 'Solution Rate (%)'},
                    color=[rate * 100 for rate in solution_rates.values()],
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100]
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No solution rate data available")
        else:
            st.info("No category data available for solution analysis")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center'>
        <p><i>🤖 TiDB Community Intelligence - Live Demo</i></p>
        <p><i>Powered by real-time GitHub API data from PingCAP/TiDB repository</i></p>
        <p><i>Created for Senior Product Manager - Developer Experience position</i></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()