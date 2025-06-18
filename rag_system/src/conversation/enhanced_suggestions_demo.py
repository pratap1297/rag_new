#!/usr/bin/env python3
"""
Enhanced Conversation Suggestions Demo
=====================================
Demonstrates the new enhanced conversation suggestions feature with UI integration.
"""

import json
from typing import Dict, Any, List
from enhanced_suggestions import EnhancedConversationSuggestions

class MockLLMClient:
    """Mock LLM client for demonstration"""
    
    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.7) -> str:
        """Generate mock responses based on prompt content"""
        
        if "follow-up questions" in prompt.lower():
            return """[
  {
    "question": "What are the specific technical requirements for this network setup?",
    "intent": "details",
    "context_hint": "Technical specifications and hardware requirements",
    "response_time": "medium",
    "relevance": 0.9,
    "icon": "🔧"
  },
  {
    "question": "How can I contact Maria Garcia for network support?",
    "intent": "action",
    "context_hint": "Contact information and support procedures",
    "response_time": "quick",
    "relevance": 0.8,
    "icon": "📞"
  },
  {
    "question": "What other network administrators work in this building?",
    "intent": "related",
    "context_hint": "Related personnel and organizational structure",
    "response_time": "medium",
    "relevance": 0.7,
    "icon": "👥"
  },
  {
    "question": "Are there any known issues with the current network configuration?",
    "intent": "clarification",
    "context_hint": "Current status and potential problems",
    "response_time": "detailed",
    "relevance": 0.75,
    "icon": "⚠️"
  },
  {
    "question": "What network monitoring tools are currently in use?",
    "intent": "exploration",
    "context_hint": "Tools and systems for network management",
    "response_time": "medium",
    "relevance": 0.65,
    "icon": "📊"
  }
]"""
        
        elif "extract explorable topics" in prompt.lower():
            return """{
  "topics": [
    {"name": "Network Security", "type": "concept", "explore_potential": "high", "icon": "🔒"},
    {"name": "Access Point Configuration", "type": "process", "explore_potential": "high", "icon": "📡"},
    {"name": "VLAN Management", "type": "system", "explore_potential": "medium", "icon": "🌐"},
    {"name": "Network Monitoring", "type": "process", "explore_potential": "high", "icon": "📊"},
    {"name": "Cisco Equipment", "type": "technology", "explore_potential": "medium", "icon": "🔧"}
  ],
  "entities": [
    {"name": "Maria Garcia", "type": "person", "context": "Senior Network Administrator", "explore_potential": "medium", "icon": "👤"},
    {"name": "Building A", "type": "location", "context": "Primary network location", "explore_potential": "high", "icon": "🏢"},
    {"name": "Cisco 3802I", "type": "product", "context": "Access point model", "explore_potential": "medium", "icon": "📡"},
    {"name": "Network Security Division", "type": "organization", "context": "Responsible department", "explore_potential": "medium", "icon": "🏛️"}
  ],
  "technical_terms": [
    {"term": "VLAN", "difficulty": "medium", "definition_available": true, "icon": "🔧"},
    {"term": "SSID", "difficulty": "easy", "definition_available": true, "icon": "📶"},
    {"term": "WPA3", "difficulty": "medium", "definition_available": true, "icon": "🔐"}
  ],
  "related_areas": [
    {"area": "Network Troubleshooting", "connection": "strong", "explore_potential": "high", "icon": "🔍"},
    {"area": "Security Protocols", "connection": "strong", "explore_potential": "high", "icon": "🛡️"},
    {"area": "Performance Optimization", "connection": "medium", "explore_potential": "medium", "icon": "⚡"},
    {"area": "Backup Systems", "connection": "medium", "explore_potential": "medium", "icon": "💾"}
  ]
}"""
        
        return "Mock response generated"

def demo_enhanced_suggestions():
    """Demonstrate the enhanced conversation suggestions feature"""
    
    print("🚀 Enhanced Conversation Suggestions Demo")
    print("=" * 50)
    
    # Initialize the enhanced suggestions system
    mock_llm = MockLLMClient()
    suggestions_engine = EnhancedConversationSuggestions(llm_client=mock_llm)
    
    # Create a mock conversation state
    mock_state = {
        'original_query': 'Who is Maria Garcia?',
        'session_id': 'demo_session_123',
        'turn_count': 2,
        'response': 'Maria Garcia is the Senior Network Administrator in the Network Security Division. She is responsible for managing the network infrastructure in Building A, including Cisco 3802I access points and VLAN configurations.',
        'search_results': [
            {
                'content': 'Maria Garcia - Senior Network Administrator, Network Security Division. Contact: maria.garcia@company.com, Phone: (555) 123-4567. Responsibilities include network infrastructure management, security protocols, and access point configuration.',
                'source': 'employee_directory.pdf',
                'score': 0.92
            },
            {
                'content': 'Building A Network Configuration: Cisco 3802I access points deployed on floors 1-5. VLAN segmentation implemented for security. Primary administrator: Maria Garcia. Backup systems managed by John Smith.',
                'source': 'network_documentation.pdf',
                'score': 0.87
            },
            {
                'content': 'Network Security Division Structure: Led by Director Sarah Johnson. Senior administrators: Maria Garcia (Building A), Robert Chen (Building B), Lisa Park (Building C). Responsible for enterprise network security and monitoring.',
                'source': 'org_chart.pdf',
                'score': 0.82
            }
        ],
        'messages': [
            {'type': 'user', 'content': 'Who is Maria Garcia?'},
            {'type': 'assistant', 'content': 'Maria Garcia is the Senior Network Administrator...'}
        ]
    }
    
    print("📋 Mock Conversation State:")
    print(f"   Query: {mock_state['original_query']}")
    print(f"   Turn Count: {mock_state['turn_count']}")
    print(f"   Sources Found: {len(mock_state['search_results'])}")
    print()
    
    # Generate enhanced response
    print("🔄 Generating Enhanced Response...")
    enhanced_response = suggestions_engine.generate_enhanced_response(mock_state)
    
    print("✅ Enhanced Response Generated!")
    print()
    
    # Display the results
    print("📝 ENHANCED RESPONSE STRUCTURE:")
    print("=" * 40)
    
    # Main response
    print(f"🤖 Main Response: {enhanced_response.get('main_response', 'N/A')[:100]}...")
    print()
    
    # Suggested questions
    suggestions = enhanced_response.get('suggested_questions', [])
    if suggestions:
        print("💡 SMART SUGGESTIONS:")
        for i, suggestion in enumerate(suggestions, 1):
            icon = suggestion.get('icon', '💬')
            question = suggestion.get('question', 'No question')
            intent = suggestion.get('intent', 'unknown')
            priority = suggestion.get('priority', 0)
            has_quick = suggestion.get('has_quick_answer', False)
            
            print(f"   {i}. {icon} {question}")
            print(f"      Intent: {intent} | Priority: {priority:.2f} | Quick Answer: {'✅' if has_quick else '❌'}")
            print()
    
    # Exploration topics
    exploration = enhanced_response.get('exploration', {})
    if exploration:
        print("🔍 EXPLORATION OPPORTUNITIES:")
        
        topics = exploration.get('topics', [])
        if topics:
            print("   📚 Topics:")
            for topic in topics:
                name = topic.get('name', 'Unknown')
                icon = topic.get('icon', '🔍')
                potential = topic.get('explore_potential', 'medium')
                print(f"      {icon} {name} (Potential: {potential})")
        
        entities = exploration.get('entities', [])
        if entities:
            print("   👥 Entities:")
            for entity in entities:
                name = entity.get('name', 'Unknown')
                entity_type = entity.get('type', 'unknown')
                icon = entity.get('icon', '📋')
                print(f"      {icon} {name} ({entity_type})")
        
        technical_terms = exploration.get('technical_terms', [])
        if technical_terms:
            print("   🔧 Technical Terms:")
            for term in technical_terms:
                term_name = term.get('term', 'Unknown')
                difficulty = term.get('difficulty', 'medium')
                icon = term.get('icon', '🔧')
                print(f"      {icon} {term_name} (Difficulty: {difficulty})")
        print()
    
    # UI Elements
    ui_elements = enhanced_response.get('ui_elements', {})
    if ui_elements:
        print("🎨 UI ELEMENTS:")
        
        suggestion_buttons = ui_elements.get('suggestion_buttons', [])
        if suggestion_buttons:
            print("   🔘 Suggestion Buttons:")
            for btn in suggestion_buttons:
                text = btn.get('text', 'Unknown')[:40] + "..."
                variant = btn.get('variant', 'secondary')
                icon = btn.get('icon', '💬')
                print(f"      {icon} {text} (Style: {variant})")
        
        topic_chips = ui_elements.get('topic_chips', [])
        if topic_chips:
            print("   🏷️ Topic Chips:")
            for chip in topic_chips:
                name = chip.get('name', 'Unknown')
                icon = chip.get('icon', '🔍')
                potential = chip.get('explore_potential', 'medium')
                print(f"      {icon} {name} (Potential: {potential})")
        print()
    
    # Interaction hints
    hints = enhanced_response.get('interaction_hints', [])
    if hints:
        print("💡 INTERACTION HINTS:")
        for hint in hints:
            print(f"   • {hint}")
        print()
    
    # Conversation insights
    insights = enhanced_response.get('insights', {})
    if insights:
        print("📊 CONVERSATION INSIGHTS:")
        coverage = insights.get('information_coverage', 'unknown')
        continuity = insights.get('topic_continuity', 0)
        print(f"   Information Coverage: {coverage}")
        print(f"   Topic Continuity: {continuity:.2f}")
        
        exploration_path = insights.get('exploration_path', [])
        if exploration_path:
            print("   Suggested Exploration Path:")
            for step in exploration_path:
                print(f"      → {step}")
        print()
    
    print("🎯 DEMO COMPLETE!")
    print("=" * 50)
    print("This demonstrates how the enhanced conversation suggestions work:")
    print("• ✅ Intelligent follow-up questions with priority ranking")
    print("• ✅ Topic exploration with interactive elements") 
    print("• ✅ Entity and technical term identification")
    print("• ✅ UI-ready components with styling information")
    print("• ✅ Contextual hints and conversation guidance")
    print("• ✅ Real-time conversation analytics")
    print()
    print("🌟 The UI will display these as clickable buttons, chips, and cards!")

def demo_ui_integration():
    """Demonstrate how the suggestions integrate with the UI"""
    
    print("\n🎨 UI INTEGRATION DEMO")
    print("=" * 30)
    
    # Simulate UI button generation
    mock_suggestions = [
        {
            'id': 'q_abc123',
            'question': 'What are the specific technical requirements for this network setup?',
            'intent': 'details',
            'icon': '🔧',
            'priority': 0.9,
            'has_quick_answer': True
        },
        {
            'id': 'q_def456',
            'question': 'How can I contact Maria Garcia for network support?',
            'intent': 'action',
            'icon': '📞',
            'priority': 0.8,
            'has_quick_answer': True
        }
    ]
    
    print("🔘 Generated UI Suggestion Buttons:")
    for suggestion in mock_suggestions:
        button_text = f"{suggestion['icon']} {suggestion['question'][:50]}..."
        priority_indicator = "🔥" if suggestion['priority'] > 0.8 else "⭐" if suggestion['priority'] > 0.6 else "💫"
        quick_indicator = "⚡" if suggestion['has_quick_answer'] else "🕐"
        
        print(f"   [{priority_indicator}{quick_indicator}] {button_text}")
        print(f"      ID: {suggestion['id']} | Intent: {suggestion['intent']}")
    
    print()
    
    # Simulate topic chips
    mock_topics = ['Network Security', 'Access Point Configuration', 'VLAN Management']
    
    print("🏷️ Generated Topic Exploration Chips:")
    for topic in mock_topics:
        print(f"   [🔍 {topic}] (Click to explore)")
    
    print()
    print("💡 In the actual UI, these become:")
    print("   • Clickable buttons that auto-fill the message input")
    print("   • Styled chips with hover effects and animations")
    print("   • Context-aware suggestions that update in real-time")
    print("   • Debug panels showing the underlying data structure")

if __name__ == "__main__":
    demo_enhanced_suggestions()
    demo_ui_integration() 