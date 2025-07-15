import streamlit as st

st.set_page_config(
    page_title="TiDB Community Intelligence - Demo for PingCAP",
    page_icon="🤖",
    layout="wide"
)

def main():
    # Header
    st.title("🤖 TiDB Community Intelligence Platform")
    st.markdown("### Demo Created for PingCAP Senior Product Manager - Developer Experience Role")
    
    # Main intro section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 👋 Hello PingCAP Hiring Team!
        
        **I've created this working demonstration specifically for the **Senior Product Manager - Developer Experience** position.
        
        ### 🎯 What This Demo Showcases
        
        This isn't just a concept - it's a **fully functional platform** that demonstrates how TiDB's incredible community engagement (37,000+ GitHub stars) could be transformed into an AI-powered developer experience platform.
        
        **Key Capabilities Demonstrated:**
        - 🔍 **AI-Powered Issue Search** - Semantic matching of developer problems with community solutions
        - 🛠️ **Tech Stack Intelligence** - Personalized recommendations based on developer's technology ecosystem  
        - 📊 **Community Analytics** - Real-time insights from TiDB's GitHub activity
        - 🚀 **Strategic Business Case** - Complete implementation roadmap with ROI analysis
        
        ### 💡 Why This Matters for PingCAP
        
        This demo shows my ability to:
        - **Think strategically** about developer experience challenges
        - **Execute technically** - this is real code pulling live TiDB data
        - **Bridge business and technical needs** - from AI implementation to business case
        - **Understand your community** - leveraged actual TiDB GitHub issues and patterns
        """)
        
        # Call to action buttons
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🚀 Launch Live Demo", type="primary", use_container_width=True):
                st.switch_page("cloud_app.py")
        
        with col_b:
            if st.button("📋 View Source Code", use_container_width=True):
                st.markdown("[GitHub Repository](https://github.com/rexieboy18/tidb-community-intelligence)")
    
    with col2:
        st.markdown("""
        ### 📊 Demo Stats
        - **Real Data**: 150+ TiDB GitHub issues
        - **AI Features**: Semantic search & pattern recognition  
        - **Technologies**: Python, Streamlit, Plotly, GitHub API
        - **Time Investment**: 20+ hours of development
        
        ### 🎯 Product Manager Skills Demonstrated
        - ✅ **Technical Vision** - AI-powered developer experience
        - ✅ **Execution** - Working prototype with real data
        - ✅ **Business Strategy** - Complete ROI framework
        - ✅ **User Focus** - Developer-centric design
        - ✅ **Community Understanding** - TiDB ecosystem analysis
        
           
    # Detailed sections
    st.divider()
    
    # Technical implementation
    st.subheader("🔧 Technical Implementation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Data Collection**
        - Live GitHub API integration
        - Real TiDB community issues
        - Automated categorization
        - Technology context extraction
        """)
    
    with col2:
        st.markdown("""
        **AI/ML Features**
        - Semantic similarity matching
        - Pattern recognition
        - Community insight generation
        - Predictive analytics framework
        """)
    
    with col3:
        st.markdown("""
        **User Experience**
        - Interactive visualizations
        - Real-time search results
        - Intuitive navigation
        - Mobile-responsive design
        """)
    
    # Business case
    st.subheader("💼 Business Impact Framework")
    
    st.markdown("""
    This demo includes a comprehensive business case showing how community intelligence could:
    """)
    
    # Create the table using Streamlit columns instead of markdown table
    st.markdown("**Projected Impact Analysis:**")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        st.markdown("**Impact Area**")
        st.write("• Developer Onboarding")
        st.write("• Support Efficiency") 
        st.write("• Community Engagement")
        st.write("• Product Differentiation")
    
    with col2:
        st.markdown("**Current Challenge**")
        st.write("• 2-3 days typical setup time")
        st.write("• 40% repetitive tickets")
        st.write("• Scattered knowledge")
        st.write("• Standard database offering")
    
    with col3:
        st.markdown("**AI-Powered Solution**")
        st.write("• Intelligent guided workflows")
        st.write("• Automated similarity matching")
        st.write("• Centralized intelligence")
        st.write("• AI-native developer experience")
    
    with col4:
        st.markdown("**Projected Improvement**")
        st.write("• 40-60% time reduction")
        st.write("• 70% ticket deflection")
        st.write("• 2x contribution rate")
        st.write("• Market leadership position")
    
    st.info("*Note: Projections based on industry benchmarks and would require validation with PingCAP data*")ship position |
    
    *Note: Projections based on industry benchmarks and would require validation with PingCAP data*
    """)
    
    # Implementation roadmap
    st.subheader("🗺️ Implementation Approach")
    
    phase1, phase2, phase3 = st.columns(3)
    
    with phase1:
        st.markdown("""
        **Phase 1: Foundation** *(3 months)*
        - Real-time data pipeline
        - Basic AI similarity matching  
        - Web interface MVP
        - Pilot with developer community
        """)
    
    with phase2:
        st.markdown("""
        **Phase 2: Intelligence** *(6 months)*
        - Advanced semantic understanding
        - Multi-modal recommendations
        - TiDB Cloud integration
        - Predictive analytics
        """)
    
    with phase3:
        st.markdown("""
        **Phase 3: Scale** *(9 months)*
        - Enterprise API platform
        - Global deployment
        - Partner integrations  
        - Advanced automation
        """)
    
    # Personal message
    st.divider()
    
    st.markdown("""
    ## 💬 A Personal Note
    
    I built this demo because I'm genuinely excited about the opportunity to transform TiDB's developer experience. 
    
    My background in **technical product management** at Starbucks taught me how to take complex technical platforms and make them accessible to users. I reduced integration complexity from 3 months to 3 weeks by focusing on self-service capabilities and intuitive design - exactly the kind of thinking that could benefit TiDB's developer community.
    
    This demo represents my **product vision, technical execution ability, and strategic thinking** - the core skills needed for this role.
    
    **I'd love to discuss how we can make this vision a reality at PingCAP!**
    """)
    
    # Footer
    st.markdown("""
    ---
    *This demo was created specifically for PingCAP's Senior Product Manager - Developer Experience role. 
    All code is available on [GitHub](https://github.com/rexieboy18/tidb-community-intelligence) under MIT license.*
    """)

if __name__ == "__main__":
    main()