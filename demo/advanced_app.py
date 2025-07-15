import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import re

# Set page config
st.set_page_config(
    page_title="TiDB Community Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    """Load the comprehensive dataset"""
    try:
        # Try multiple possible locations for data files
        data_paths = [
            '../data/',  # Standard location
            '../src/data/',  # If data is in src folder
            './data/',   # If running from root
            '../'        # If files are in parent directory
        ]
        
        issues_file = None
        analytics_file = None
        
        for path in data_paths:
            try:
                with open(f'{path}tidb_issues.json', 'r') as f:
                    issues = json.load(f)
                    issues_file = f'{path}tidb_issues.json'
                break
            except FileNotFoundError:
                continue
        
        if not issues_file:
            raise FileNotFoundError("Could not find tidb_issues.json")
        
        # Try to find analytics file in same location
        analytics_path = issues_file.replace('tidb_issues.json', 'analytics.json')
        try:
            with open(analytics_path, 'r') as f:
                analytics = json.load(f)
        except FileNotFoundError:
            # If analytics.json doesn't exist, try summary.json
            summary_path = issues_file.replace('tidb_issues.json', 'summary.json')
            try:
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                    # Convert summary format to analytics format
                    analytics = {
                        'summary': summary,
                        'categories': {'distribution': summary.get('categories', {})},
                        'technology': {'usage': summary.get('tech_usage', {})},
                        'temporal': {},
                        'community': {}
                    }
            except FileNotFoundError:
                # Create minimal analytics if no file found
                analytics = {
                    'summary': {
                        'total_issues': len(issues),
                        'solution_rate': sum(1 for i in issues if i.get('has_solution', False)) / len(issues),
                        'avg_engagement': sum(i.get('engagement_score', 0) for i in issues) / len(issues)
                    },
                    'categories': {'distribution': {}},
                    'technology': {'usage': {}},
                    'temporal': {},
                    'community': {}
                }
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(issues)
        if not df.empty and 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['updated_at'] = pd.to_datetime(df['updated_at'])
        
        st.success(f"✅ Loaded {len(issues)} issues from {issues_file}")
        return issues, analytics, df
        
    except Exception as e:
        st.error(f"⚠️ Could not load data files. Error: {str(e)}")
        st.info("Please make sure you've run the data collector:")
        st.code("cd src && python simple_collector_basic.py", language="bash")
        st.info("Or for advanced features:")
        st.code("cd src && python data_collector.py", language="bash")
        
        # Show current directory for debugging
        import os
        st.write("**Current directory:**", os.getcwd())
        st.write("**Available files:**")
        
        # Check multiple locations
        locations_to_check = ['../data/', '../src/data/', '../src/', '../', './data/', './']
        for location in locations_to_check:
            try:
                files = os.listdir(location)
                json_files = [f for f in files if f.endswith('.json')]
                if json_files:
                    st.write(f"- {location}: {json_files}")
            except:
                pass
        
        return [], {}, pd.DataFrame()

def calculate_similarity(query, issue):
    """Advanced similarity calculation"""
    query_words = set(query.lower().split())
    
    # Weight different parts of the issue
    title_words = set(issue['title'].lower().split())
    body_words = set((issue['body'] or '').lower().split())
    label_words = set(' '.join(issue['labels']).lower().split())
    tech_words = set(issue.get('tech_context', []))
    
    # Calculate overlaps with different weights
    title_overlap = len(query_words.intersection(title_words)) * 3
    body_overlap = len(query_words.intersection(body_words)) * 1
    label_overlap = len(query_words.intersection(label_words)) * 2
    tech_overlap = len(query_words.intersection(tech_words)) * 4
    
    total_overlap = title_overlap + body_overlap + label_overlap + tech_overlap
    max_possible = len(query_words) * 4  # Max weight is 4 for tech
    
    similarity = total_overlap / max_possible if max_possible > 0 else 0
    return min(similarity, 1.0)

def find_similar_issues(query, issues, top_k=5):
    """Find most similar issues using advanced matching"""
    if not query.strip():
        return []
    
    similarities = []
    for issue in issues:
        similarity = calculate_similarity(query, issue)
        if similarity > 0:
            similarities.append({
                'issue': issue,
                'similarity': similarity,
                'confidence': get_solution_confidence(issue)
            })
    
    # Sort by similarity and confidence
    similarities.sort(key=lambda x: (x['similarity'], x['confidence']), reverse=True)
    return similarities[:top_k]

def get_solution_confidence(issue):
    """Calculate confidence in the solution"""
    confidence = 0.0
    
    if issue['has_solution']:
        confidence += 0.5
    
    # More comments usually mean better solutions
    confidence += min(issue['comments_count'] * 0.02, 0.3)
    
    # Recent issues might have more relevant solutions
    if issue.get('is_recent', False):
        confidence += 0.1
    
    # High engagement score indicates community attention
    confidence += min(issue.get('engagement_score', 0) * 0.01, 0.1)
    
    return min(confidence, 1.0)

def get_tech_stack_insights(selected_tech, issues, analytics):
    """Generate comprehensive tech stack insights"""
    insights = []
    
    for tech in selected_tech:
        # Find relevant issues
        relevant_issues = [
            issue for issue in issues 
            if tech.lower() in [t.lower() for t in issue.get('tech_context', [])]
        ]
        
        if relevant_issues:
            # Calculate metrics
            total_issues = len(relevant_issues)
            solved_issues = sum(1 for issue in relevant_issues if issue['has_solution'])
            solution_rate = solved_issues / total_issues if total_issues > 0 else 0
            
            # Category breakdown
            categories = Counter(issue['category'] for issue in relevant_issues)
            
            # Recent trend
            recent_issues = [issue for issue in relevant_issues if issue.get('is_recent', False)]
            trend = "📈 Increasing" if len(recent_issues) / total_issues > 0.3 else "📊 Stable"
            
            # Average engagement
            avg_engagement = np.mean([issue.get('engagement_score', 0) for issue in relevant_issues])
            
            insights.append({
                'technology': tech,
                'total_issues': total_issues,
                'solution_rate': solution_rate,
                'trend': trend,
                'avg_engagement': avg_engagement,
                'top_categories': dict(categories.most_common(3)),
                'recent_count': len(recent_issues),
                'sample_issues': relevant_issues[:3]
            })
    
    return insights

def create_category_sunburst(analytics):
    """Create sunburst chart for issue categories"""
    categories = analytics.get('categories', {}).get('distribution', {})
    
    if not categories:
        return None
    
    # Prepare data for sunburst
    labels = ['All Issues'] + list(categories.keys())
    parents = [''] + ['All Issues'] * len(categories)
    values = [sum(categories.values())] + list(categories.values())
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentParent}<extra></extra>',
        maxdepth=2,
    ))
    
    fig.update_layout(
        title="Issue Categories Distribution",
        height=400,
        font_size=12
    )
    
    return fig

def create_technology_network(analytics):
    """Create network visualization of technology combinations"""
    combinations = analytics.get('technology', {}).get('combinations', [])
    
    if not combinations:
        return None
    
    # Prepare data for network
    technologies = set()
    edges = []
    
    for combo in combinations[:10]:  # Top 10 combinations
        tech1, tech2 = combo['technologies']
        technologies.add(tech1)
        technologies.add(tech2)
        edges.append({
            'source': tech1,
            'target': tech2,
            'weight': combo['count']
        })
    
    # Create adjacency matrix for heatmap
    tech_list = list(technologies)
    matrix = np.zeros((len(tech_list), len(tech_list)))
    
    for edge in edges:
        i = tech_list.index(edge['source'])
        j = tech_list.index(edge['target'])
        matrix[i][j] = edge['weight']
        matrix[j][i] = edge['weight']  # Make symmetric
    
    fig = px.imshow(
        matrix,
        x=tech_list,
        y=tech_list,
        title="Technology Co-occurrence Matrix",
        color_continuous_scale='Viridis',
        aspect='auto'
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Technologies",
        yaxis_title="Technologies"
    )
    
    return fig

def create_temporal_analysis(df):
    """Create temporal analysis charts"""
    if df.empty:
        return None, None
    
    # Monthly trend
    df['month'] = df['created_at'].dt.to_period('M')
    monthly_counts = df.groupby(['month', 'category']).size().reset_index(name='count')
    monthly_counts['month_str'] = monthly_counts['month'].astype(str)
    
    fig1 = px.line(
        monthly_counts,
        x='month_str',
        y='count',
        color='category',
        title='Monthly Issue Trends by Category',
        labels={'month_str': 'Month', 'count': 'Number of Issues'}
    )
    fig1.update_layout(height=400)
    
    # Solution rate over time
    monthly_solution = df.groupby('month').agg({
        'has_solution': 'mean',
        'engagement_score': 'mean'
    }).reset_index()
    monthly_solution['month_str'] = monthly_solution['month'].astype(str)
    
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig2.add_trace(
        go.Scatter(
            x=monthly_solution['month_str'],
            y=monthly_solution['has_solution'] * 100,
            name="Solution Rate (%)",
            line=dict(color='green')
        ),
        secondary_y=False,
    )
    
    fig2.add_trace(
        go.Scatter(
            x=monthly_solution['month_str'],
            y=monthly_solution['engagement_score'],
            name="Avg Engagement",
            line=dict(color='blue')
        ),
        secondary_y=True,
    )
    
    fig2.update_xaxes(title_text="Month")
    fig2.update_yaxes(title_text="Solution Rate (%)", secondary_y=False)
    fig2.update_yaxes(title_text="Engagement Score", secondary_y=True)
    fig2.update_layout(title_text="Solution Rate and Engagement Trends", height=400)
    
    return fig1, fig2

def main():
    # Custom CSS
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .insight-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("🤖 TiDB Community Intelligence Platform")
    st.markdown("*Transforming 37,000+ GitHub stars into actionable AI-powered insights*")
    
    # Load data
    issues, analytics, df = load_data()
    
    if not issues:
        st.stop()
    
    # Sidebar
    st.sidebar.header("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a feature:",
        [
            "🏠 Executive Dashboard",
            "🔍 AI Issue Search",
            "🛠️ Tech Stack Intelligence", 
            "📊 Community Analytics",
            "🎯 Strategic Insights",
            "🚀 Implementation Roadmap"
        ]
    )
    
    if page == "🏠 Executive Dashboard":
        st.header("📊 Executive Dashboard")
        
        # Key Metrics Row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Issues Analyzed",
                analytics['summary']['total_issues'],
                help="Issues collected from TiDB GitHub repository"
            )
        
        with col2:
            solution_rate = analytics['summary']['solution_rate']
            st.metric(
                "Community Solution Rate",
                f"{solution_rate:.1%}",
                delta=f"+{(solution_rate - 0.6):.1%}" if solution_rate > 0.6 else None,
                help="Percentage of issues that receive community solutions"
            )
        
        with col3:
            st.metric(
                "Active Categories",
                len(analytics['categories']['distribution']),
                help="Different types of issues identified"
            )
        
        with col4:
            avg_engagement = analytics['summary']['avg_engagement']
            st.metric(
                "Avg Engagement Score",
                f"{avg_engagement:.1f}",
                help="Community engagement level (comments, labels, assignees)"
            )
        
        with col5:
            tech_count = len(analytics['technology']['usage'])
            st.metric(
                "Technologies Tracked",
                tech_count,
                help="Different technologies mentioned in issues"
            )
        
        st.divider()
        
        # Visual Analytics
        col1, col2 = st.columns(2)
        
        with col1:
            # Category distribution
            fig_sunburst = create_category_sunburst(analytics)
            if fig_sunburst:
                st.plotly_chart(fig_sunburst, use_container_width=True)
        
        with col2:
            # Solution rates by category
            categories = analytics['categories']['distribution']
            solution_rates = analytics['categories']['solution_rates']
            
            if categories and solution_rates:
                fig = px.bar(
                    x=list(solution_rates.keys()),
                    y=[rate * 100 for rate in solution_rates.values()],
                    title="Solution Rate by Category (%)",
                    color=[rate * 100 for rate in solution_rates.values()],
                    color_continuous_scale='RdYlGn',
                    labels={'x': 'Category', 'y': 'Solution Rate (%)'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Technology landscape
        st.subheader("🔧 Technology Landscape")
        fig_tech = create_technology_network(analytics)
        if fig_tech:
            st.plotly_chart(fig_tech, use_container_width=True)
        
        # Temporal trends
        if not df.empty:
            st.subheader("📈 Temporal Analysis")
            fig_trend, fig_solution = create_temporal_analysis(df)
            
            col1, col2 = st.columns(2)
            with col1:
                if fig_trend:
                    st.plotly_chart(fig_trend, use_container_width=True)
            with col2:
                if fig_solution:
                    st.plotly_chart(fig_solution, use_container_width=True)
    
    elif page == "🔍 AI Issue Search":
        st.header("🔍 AI-Powered Issue Search")
        st.markdown("*Find similar issues using advanced semantic matching*")
        
        # Search interface
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_area(
                "Describe your TiDB issue:",
                placeholder="e.g., TiDB connection timeout in Kubernetes cluster with high load",
                height=100,
                help="Include specific error messages, technologies, and context for better results"
            )
        
        with col2:
            st.markdown("**🎯 Search Tips:**")
            st.markdown("• Include error messages")
            st.markdown("• Mention tech stack")
            st.markdown("• Describe context")
            st.markdown("• Use specific terms")
        
        if query:
            with st.spinner("🔍 Analyzing with AI..."):
                similar_issues = find_similar_issues(query, issues)
            
            if similar_issues:
                st.subheader(f"🎯 Found {len(similar_issues)} Similar Issues")
                
                for i, result in enumerate(similar_issues):
                    issue = result['issue']
                    similarity = result['similarity']
                    confidence = result['confidence']
                    
                    # Issue card with enhanced styling
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin: 8px 0; background: white;">
                            <h4 style="color: #1f77b4; margin-top: 0;">#{i+1}: {issue['title']}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Category:** {issue['category'].title()}")
                            st.write(f"**Status:** {'✅ Solved' if issue['has_solution'] else '🔄 Open'}")
                            st.write(f"**Comments:** {issue['comments_count']}")
                            
                            if issue.get('tech_context'):
                                tech_tags = ' '.join([f"`{tech}`" for tech in issue['tech_context'][:5]])
                                st.markdown(f"**Technologies:** {tech_tags}")
                        
                        with col2:
                            # Similarity gauge
                            similarity_pct = similarity * 100
                            color = "🟢" if similarity > 0.7 else "🟡" if similarity > 0.4 else "🔴"
                            st.metric("Similarity", f"{similarity_pct:.0f}%", help="How similar this issue is to your query")
                            
                            # Confidence gauge
                            confidence_pct = confidence * 100
                            conf_color = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
                            st.metric("Solution Confidence", f"{confidence_pct:.0f}%", help="How confident we are in the solution quality")
                        
                        with col3:
                            st.write(f"**Engagement:** {issue.get('engagement_score', 0):.0f}")
                            st.write(f"**Recent:** {'Yes' if issue.get('is_recent') else 'No'}")
                            
                            if issue.get('labels'):
                                st.write("**Top Labels:**")
                                for label in issue['labels'][:3]:
                                    st.code(label, language=None)
                        
                        # Expandable details
                        with st.expander("View Details & Solution Insights"):
                            if issue['body']:
                                st.write("**Issue Description:**")
                                description = issue['body'][:500] + "..." if len(issue['body']) > 500 else issue['body']
                                st.write(description)
                            
                            if issue.get('error_patterns'):
                                st.write("**Error Patterns Found:**")
                                for pattern in issue['error_patterns'][:3]:
                                    st.code(pattern)
                            
                            # AI-generated insights
                            st.write("**🤖 AI Insights:**")
                            if issue['has_solution']:
                                st.success(f"✅ This issue was resolved with {issue['comments_count']} community comments")
                            
                            if issue.get('tech_context'):
                                common_tech = ', '.join(issue['tech_context'][:3])
                                st.info(f"🔧 Common in {common_tech} environments")
                            
                            if similarity > 0.8:
                                st.success("🎯 Very high similarity - this solution likely applies to your case")
                            elif similarity > 0.5:
                                st.warning("🎯 Good similarity - solution may need adaptation")
                        
                        st.divider()
            else:
                st.info("💡 No similar issues found. Try different keywords or broader terms.")
                
                # Suggestion engine
                st.subheader("🤖 AI Suggestions")
                st.markdown("""
                **Try these search strategies:**
                
                🔍 **For Error Messages:**
                - Include the exact error text in quotes
                - Mention the component (TiKV, PD, TiFlash)
                
                🛠️ **For Performance Issues:**
                - Describe the workload type
                - Include metrics (QPS, latency, etc.)
                
                ⚙️ **For Configuration:**
                - Mention your deployment method
                - Include version information
                """)
    
    elif page == "🛠️ Tech Stack Intelligence":
        st.header("🛠️ Tech Stack Intelligence")
        st.markdown("*Get personalized insights based on your technology ecosystem*")
        
        # Tech stack selector
        available_technologies = list(analytics.get('technology', {}).get('usage', {}).keys())
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_tech = st.multiselect(
                "Select your technology stack:",
                available_technologies,
                default=available_technologies[:3] if available_technologies else [],
                help="Choose technologies you're using with TiDB"
            )
        
        with col2:
            st.markdown("**🔧 Available Technologies:**")
            tech_usage = analytics.get('technology', {}).get('usage', {})
            for tech, count in list(tech_usage.items())[:8]:
                st.write(f"• {tech.title()}: {count} mentions")
        
        if selected_tech:
            insights = get_tech_stack_insights(selected_tech, issues, analytics)
            
            # Summary metrics
            st.subheader("📊 Stack Overview")
            cols = st.columns(len(selected_tech))
            
            for i, insight in enumerate(insights):
                with cols[i]:
                    st.metric(
                        insight['technology'].title(),
                        f"{insight['total_issues']} issues",
                        f"{insight['solution_rate']:.0%} solved"
                    )
            
            # Detailed analysis for each technology
            for insight in insights:
                st.subheader(f"🔧 {insight['technology'].title()} Deep Dive")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Issues", insight['total_issues'])
                
                with col2:
                    st.metric("Solution Rate", f"{insight['solution_rate']:.1%}")
                
                with col3:
                    st.metric("Trend", insight['trend'])
                
                with col4:
                    st.metric("Avg Engagement", f"{insight['avg_engagement']:.1f}")
                
                # Category breakdown
                if insight['top_categories']:
                    st.write("**Common Issue Types:**")
                    category_df = pd.DataFrame([
                        {'Category': cat, 'Count': count, 'Percentage': f"{count/insight['total_issues']*100:.1f}%"}
                        for cat, count in insight['top_categories'].items()
                    ])
                    st.dataframe(category_df, use_container_width=True)
                
                # Sample issues
                if insight['sample_issues']:
                    with st.expander(f"Sample {insight['technology'].title()} Issues"):
                        for issue in insight['sample_issues']:
                            status = "✅" if issue['has_solution'] else "🔄"
                            st.write(f"{status} **{issue['title']}** ({issue['comments_count']} comments)")
                
                st.divider()
            
            # Cross-technology insights
            st.subheader("🔗 Technology Interactions")
            
            # Find issues that mention multiple selected technologies
            multi_tech_issues = []
            for issue in issues:
                issue_tech = [t.lower() for t in issue.get('tech_context', [])]
                selected_lower = [t.lower() for t in selected_tech]
                
                if len(set(issue_tech).intersection(set(selected_lower))) >= 2:
                    multi_tech_issues.append(issue)
            
            if multi_tech_issues:
                st.write(f"**Found {len(multi_tech_issues)} issues involving multiple technologies from your stack:**")
                
                # Show patterns
                pattern_categories = Counter(issue['category'] for issue in multi_tech_issues)
                
                fig = px.bar(
                    x=list(pattern_categories.keys()),
                    y=list(pattern_categories.values()),
                    title=f"Common Issues When Using {', '.join(selected_tech)} Together",
                    labels={'x': 'Issue Category', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # AI Recommendations
            st.subheader("🤖 AI-Powered Recommendations")
            
            recommendations = []
            
            for insight in insights:
                tech = insight['technology']
                if insight['solution_rate'] < 0.7:
                    recommendations.append(f"📚 **{tech.title()}**: Solution rate is {insight['solution_rate']:.0%}. Consider creating more documentation for this stack.")
                
                if insight['recent_count'] > insight['total_issues'] * 0.4:
                    recommendations.append(f"📈 **{tech.title()}**: High recent activity. Monitor for emerging patterns.")
                
                if insight['avg_engagement'] > 15:
                    recommendations.append(f"🔥 **{tech.title()}**: High community engagement. Great opportunity for knowledge sharing.")
            
            if recommendations:
                for rec in recommendations:
                    st.markdown(rec)
            else:
                st.success("🎉 Your tech stack shows healthy community support patterns!")
    
    elif page == "📊 Community Analytics":
        st.header("📊 Advanced Community Analytics")
        
        # Community health metrics
        st.subheader("🏥 Community Health Score")
        
        # Calculate health score
        health_metrics = {
            'Solution Rate': analytics['summary']['solution_rate'] * 100,
            'Engagement Level': min(analytics['summary']['avg_engagement'] / 10 * 100, 100),
            'Recent Activity': (analytics['summary'].get('recent_issues', 0) / analytics['summary']['total_issues']) * 100,
            'Category Diversity': min(len(analytics['categories']['distribution']) / 8 * 100, 100)
        }
        
        overall_health = np.mean(list(health_metrics.values()))
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Health score gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = overall_health,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Community Health Score"},
                delta = {'reference': 75},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            # Health metrics breakdown
            st.write("**Health Metrics Breakdown:**")
            
            for metric, score in health_metrics.items():
                progress_color = "🟢" if score > 75 else "🟡" if score > 50 else "🔴"
                st.write(f"{progress_color} **{metric}**: {score:.1f}%")
                st.progress(score / 100)
        
        # Top contributors analysis
        st.subheader("👥 Community Contributors")
        
        if 'community' in analytics and 'top_contributors' in analytics['community']:
            contributors = analytics['community']['top_contributors']
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top contributors chart
                fig = px.bar(
                    x=list(contributors.values())[:10],
                    y=list(contributors.keys())[:10],
                    orientation='h',
                    title="Top 10 Contributors by Issues Created",
                    labels={'x': 'Number of Issues', 'y': 'Contributor'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Contributor insights
                st.write("**📈 Contributor Insights:**")
                
                total_contributors = len(contributors)
                top_10_issues = sum(list(contributors.values())[:10])
                
                st.metric("Total Contributors", total_contributors)
                st.metric("Top 10 Contribution %", f"{top_10_issues/analytics['summary']['total_issues']*100:.1f}%")
                
                # Community distribution
                single_issue = sum(1 for count in contributors.values() if count == 1)
                st.write(f"**Single Issue Contributors:** {single_issue} ({single_issue/total_contributors*100:.1f}%)")
                
                power_users = sum(1 for count in contributors.values() if count >= 5)
                st.write(f"**Power Users (5+ issues):** {power_users} ({power_users/total_contributors*100:.1f}%)")
        
        # Resolution time analysis
        if 'temporal' in analytics and 'resolution_times' in analytics['temporal']:
            st.subheader("⏱️ Resolution Time Analysis")
            
            resolution_data = analytics['temporal']['resolution_times']
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'avg_hours' in resolution_data:
                    avg_hours = resolution_data['avg_hours']
                    st.metric("Average Resolution Time", f"{avg_hours:.1f} hours")
                
                if 'median_hours' in resolution_data:
                    median_hours = resolution_data['median_hours']
                    st.metric("Median Resolution Time", f"{median_hours:.1f} hours")
            
            with col2:
                if 'by_category' in resolution_data:
                    category_times = resolution_data['by_category']
                    
                    fig = px.bar(
                        x=list(category_times.keys()),
                        y=list(category_times.values()),
                        title="Average Resolution Time by Category (Hours)",
                        labels={'x': 'Category', 'y': 'Hours'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
    
    elif page == "🎯 Strategic Insights":
        st.header("🎯 Strategic AI Insights")
        st.markdown("*Data-driven recommendations for TiDB developer experience*")
        
        # Key opportunity areas
        st.subheader("🚀 Top Opportunity Areas")
        
        opportunities = [
            {
                'area': '🎓 Developer Onboarding',
                'priority': 'High',
                'impact': 'High',
                'description': 'Create AI-powered onboarding paths based on tech stack',
                'metrics': f"{analytics['summary']['total_issues']} issues could be prevented",
                'action': 'Build interactive tutorials for top 5 issue categories'
            },
            {
                'area': '🤖 Automated Support',
                'priority': 'High', 
                'impact': 'Medium',
                'description': 'Implement similarity-based issue resolution',
                'metrics': f"{analytics['summary']['solution_rate']:.0%} current solution rate",
                'action': 'Deploy AI assistant for instant issue matching'
            },
            {
                'area': '📚 Dynamic Documentation',
                'priority': 'Medium',
                'impact': 'High', 
                'description': 'Generate contextual docs from community solutions',
                'metrics': f"{len(analytics['technology']['usage'])} tech stacks to cover",
                'action': 'Auto-generate tech-specific guides'
            },
            {
                'area': '🔮 Predictive Analytics',
                'priority': 'Medium',
                'impact': 'Medium',
                'description': 'Predict and prevent common issues',
                'metrics': f"{len(analytics['categories']['distribution'])} categories to monitor",
                'action': 'Build early warning system for breaking changes'
            }
        ]
        
        for opp in opportunities:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    priority_color = "🔴" if opp['priority'] == 'High' else "🟡"
                    impact_color = "🟢" if opp['impact'] == 'High' else "🟡"
                    
                    st.markdown(f"**{opp['area']}**")
                    st.write(opp['description'])
                    st.write(f"Priority: {priority_color} {opp['priority']} | Impact: {impact_color} {opp['impact']}")
                
                with col2:
                    st.metric("Key Metric", opp['metrics'])
                
                with col3:
                    st.write("**Recommended Action:**")
                    st.write(opp['action'])
                
                st.divider()
        
        # ROI projections
        st.subheader("💰 ROI Projections")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🎯 Developer Productivity**
            - 50% reduction in onboarding time
            - 70% fewer repetitive support tickets  
            - 3x faster issue resolution
            
            **Estimated Impact:** $2M+ annual savings
            """)
        
        with col2:
            st.markdown("""
            **📈 Community Growth**
            - 40% increase in solution rate
            - 2x more community contributions
            - 60% improvement in developer NPS
            
            **Estimated Impact:** 25% faster user acquisition
            """)
        
        with col3:
            st.markdown("""
            **🚀 Product Differentiation**
            - First database with AI developer experience
            - Unique community-powered intelligence
            - Competitive moat through network effects
            
            **Estimated Impact:** 15% market share growth
            """)
        
        # Implementation timeline
        st.subheader("📅 Implementation Timeline")
        
        timeline_data = {
            'Phase': ['Phase 1: Foundation', 'Phase 2: Intelligence', 'Phase 3: Scale'],
            'Duration': ['3 months', '6 months', '9 months'],
            'Key Deliverables': [
                'Basic AI search, Issue categorization, Community data pipeline',
                'Advanced recommendations, Predictive analytics, Multi-modal AI',
                'Enterprise integration, Global deployment, Advanced automation'
            ],
            'Success Metrics': [
                '80% search accuracy, 50% faster onboarding',
                '90% solution confidence, 70% ticket reduction', 
                '95% automation rate, 2x community growth'
            ]
        }
        
        timeline_df = pd.DataFrame(timeline_data)
        st.dataframe(timeline_df, use_container_width=True)
    
    elif page == "🚀 Implementation Roadmap":
        st.header("🚀 Implementation Roadmap")
        st.markdown("*Detailed technical and business implementation plan*")
        
        # Technical architecture
        st.subheader("🏗️ Technical Architecture")
        
        st.markdown("""
        ```
        ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
        │   Data Layer    │    │   AI/ML Layer    │    │  Application    │
        │                 │    │                  │    │     Layer       │
        │ • GitHub API    │────│ • Embeddings     │────│ • Web Interface │
        │ • Community     │    │ • Similarity     │    │ • API Gateway   │
        │   Forums        │    │ • Classification │    │ • Mobile App    │
        │ • Support Logs  │    │ • Clustering     │    │ • CLI Tools     │
        └─────────────────┘    └──────────────────┘    └─────────────────┘
                │                        │                        │
        ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
        │ Storage Layer   │    │ Processing Layer │    │  Integration    │
        │                 │    │                  │    │     Layer       │
        │ • Vector DB     │    │ • Real-time      │    │ • TiDB Cloud    │
        │ • Time Series   │    │ • Batch Jobs     │    │ • Support Tools │
        │ • Graph DB      │    │ • Event Stream   │    │ • Dev Tools     │
        └─────────────────┘    └──────────────────┘    └─────────────────┘
        ```
        """)
        
        # Development phases
        tabs = st.tabs(["Phase 1: Foundation", "Phase 2: Intelligence", "Phase 3: Scale"])
        
        with tabs[0]:
            st.subheader("🎯 Phase 1: Foundation (Months 1-3)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **🔧 Technical Deliverables:**
                - [ ] Real-time GitHub data ingestion pipeline
                - [ ] Basic NLP processing (sentence transformers)
                - [ ] Vector database setup (Pinecone/Weaviate)
                - [ ] Web interface prototype (React/Streamlit)
                - [ ] Issue categorization system
                - [ ] Simple similarity matching
                
                **📊 Success Metrics:**
                - 80% categorization accuracy
                - <2 second search response time
                - 100% data pipeline uptime
                """)
            
            with col2:
                st.markdown("""
                **👥 Team Requirements:**
                - 1 Senior Backend Engineer
                - 1 ML Engineer
                - 1 Frontend Engineer
                - 0.5 DevOps Engineer
                - 1 Product Manager (you!)
                
                **💰 Estimated Cost:**
                - Team: $150K/month
                - Infrastructure: $5K/month
                - Tools/Services: $2K/month
                """)
        
        with tabs[1]:
            st.subheader("🧠 Phase 2: Intelligence (Months 4-6)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **🔧 Technical Deliverables:**
                - [ ] Advanced semantic search with context
                - [ ] Multi-modal recommendations (code + docs)
                - [ ] Predictive issue classification
                - [ ] Community feedback loops
                - [ ] Performance optimization engine
                - [ ] Integration with TiDB Cloud console
                
                **📊 Success Metrics:**
                - 90% solution confidence accuracy
                - 70% reduction in support tickets
                - 50% faster developer onboarding
                """)
            
            with col2:
                st.markdown("""
                **👥 Team Scale-up:**
                - +1 Senior ML Engineer
                - +1 Data Engineer
                - +0.5 UX Designer
                - +1 Integration Engineer
                
                **💰 Estimated Cost:**
                - Team: $220K/month
                - Infrastructure: $15K/month
                - ML Services: $8K/month
                """)
        
        with tabs[2]:
            st.subheader("🌍 Phase 3: Scale (Months 7-9)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **🔧 Technical Deliverables:**
                - [ ] Enterprise-grade API platform
                - [ ] Multi-language support (i18n)
                - [ ] Advanced analytics dashboard
                - [ ] Partner ecosystem integrations
                - [ ] Mobile applications
                - [ ] Global CDN deployment
                
                **📊 Success Metrics:**
                - 95% system availability
                - 500K+ monthly active users
                - 40+ ecosystem integrations
                """)
            
            with col2:
                st.markdown("""
                **👥 Team Expansion:**
                - +1 Platform Engineer
                - +1 Mobile Engineer
                - +1 DevRel Engineer
                - +2 Integration Engineers
                
                **💰 Estimated Cost:**
                - Team: $300K/month
                - Infrastructure: $40K/month
                - Global Services: $15K/month
                """)
        
        # Risk mitigation
        st.subheader("⚠️ Risk Mitigation")
        
        risks = [
            {
                'risk': 'AI Model Accuracy',
                'probability': 'Medium',
                'impact': 'High',
                'mitigation': 'Continuous training, human feedback loops, A/B testing'
            },
            {
                'risk': 'Data Quality Issues',
                'probability': 'Medium',
                'impact': 'Medium', 
                'mitigation': 'Automated data validation, community moderation, expert review'
            },
            {
                'risk': 'Scalability Challenges',
                'probability': 'Low',
                'impact': 'High',
                'mitigation': 'Cloud-native architecture, horizontal scaling, caching layers'
            },
            {
                'risk': 'Community Adoption',
                'probability': 'Low',
                'impact': 'Medium',
                'mitigation': 'Developer-first design, gradual rollout, incentive programs'
            }
        ]
        
        risk_df = pd.DataFrame(risks)
        st.dataframe(risk_df, use_container_width=True)
        
        # Success factors
        st.subheader("🎯 Critical Success Factors")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎪 Product Success:**
            - Developer-obsessed user experience
            - High accuracy AI recommendations  
            - Seamless integration with existing workflows
            - Strong community feedback loops
            - Continuous learning and improvement
            """)
        
        with col2:
            st.markdown("""
            **📈 Business Success:**
            - Clear ROI demonstration
            - Strong partnership ecosystem
            - Effective go-to-market strategy
            - Competitive differentiation
            - Scalable monetization model
            """)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <h4>🤖 TiDB Community Intelligence Platform</h4>
        <p><i>Transforming developer experience through AI-powered community insights</i></p>
        <p><i>Demo created for PingCAP Senior Product Manager - Developer Experience position</i></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()