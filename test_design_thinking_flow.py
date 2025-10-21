#!/usr/bin/env python3
"""
Design Thinking Game Flow Testing Script

This script validates the complete user experience and game flow for the 
Design Thinking educational game, testing all LPAR (Learn-Practice-Apply-Reflect)
components across all five missions.

Usage: python test_design_thinking_flow.py [--verbose] [--mission <mission_name>]
"""

import os
import sys
import json
import time
from pathlib import Path
import argparse

# Add Django project to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Test data structure for simulating user journey
DESIGN_THINKING_FLOW_TEST = {
    "test_name": "Complete Design Thinking Game Flow",
    "description": "Tests the entire LPAR structure across all five DT missions",
    "missions": [
        {
            "name": "empathy",
            "title": "🔍 Empathy Mission",
            "template": "templates/group_learning/design_thinking/missions/empathy.html",
            "required_elements": {
                "learn_phase": [
                    "Learn: Mastering Empathy in Design",
                    "What is Empathy?",
                    "Key Principles",
                    "empathy_mission_learn"
                ],
                "practice_phase": [
                    "Practice: Empathy Simulation", 
                    "user_persona_builder",
                    "practice_scenarios"
                ],
                "apply_phase": [
                    "Apply: Real-World Observation Mission",
                    "empathy-toolkit",
                    "observation-card",
                    "emotion-selector"
                ],
                "reflect_phase": [
                    "Reflect: Understanding Your Empathy Journey",
                    "reflection-questions",
                    "key-learnings",
                    "apply-this-learning"
                ]
            },
            "session_data": ["designThinking_observations", "designThinking_userPersona"],
            "expected_outputs": ["user observations", "persona data", "emotion mapping"]
        },
        {
            "name": "define",
            "title": "🎯 Define Mission", 
            "template": "templates/group_learning/design_thinking/missions/define.html",
            "required_elements": {
                "learn_phase": [
                    "Learn: Understanding the Define Phase",
                    "What is Define?",
                    "Key Principles"
                ],
                "practice_phase": [
                    "Practice: POV Statement Framework",
                    "pov-formula",
                    "practice-examples"
                ],
                "apply_phase": [
                    "Apply: Build Your POV Statement",
                    "pov-builder",
                    "pov-statement-preview"
                ],
                "reflect_phase": [
                    "Reflect: Understanding Your Define Journey",
                    "reflection-questions",
                    "key-learnings"
                ]
            },
            "session_data": ["designThinking_povStatement"],
            "expected_outputs": ["POV statement", "problem definition", "HMW questions"]
        },
        {
            "name": "ideate",
            "title": "💡 Ideate Mission",
            "template": "templates/group_learning/design_thinking/missions/ideate.html", 
            "required_elements": {
                "learn_phase": [
                    "Learn: The Power of Creative Ideation",
                    "What is Ideation?",
                    "Key Principles"
                ],
                "practice_phase": [
                    "Practice: Creativity Warm-Up",
                    "creativity-boosters",
                    "ideation-methods"
                ],
                "apply_phase": [
                    "Apply: Solution Generation Mission",
                    "ideation-toolkit",
                    "method-selector"
                ],
                "reflect_phase": [
                    "Reflect: Understanding Your Creative Process",
                    "reflection-questions",
                    "key-learnings"
                ]
            },
            "session_data": ["designThinking_ideas"],
            "expected_outputs": ["creative ideas", "ideation methods", "solution concepts"]
        },
        {
            "name": "prototype",
            "title": "🔧 Prototype Mission",
            "template": "templates/group_learning/design_thinking/missions/prototype.html",
            "required_elements": {
                "learn_phase": [
                    "Learn: The Art of Rapid Prototyping",
                    "What is Prototyping?",
                    "Key Principles"
                ],
                "practice_phase": [
                    "Practice: Prototype Planning Workshop",
                    "prototype-types",
                    "planning-exercise"
                ],
                "apply_phase": [
                    "Apply: Build Your Prototype",
                    "prototype-toolkit",
                    "prototype-builder"
                ],
                "reflect_phase": [
                    "Reflect: Understanding Your Prototyping Journey",
                    "reflection-questions",
                    "key-learnings"
                ]
            },
            "session_data": ["designThinking_prototype"],
            "expected_outputs": ["prototype plan", "materials list", "testing framework"]
        },
        {
            "name": "showcase",
            "title": "🏆 Showcase Mission",
            "template": "templates/group_learning/design_thinking/missions/showcase.html",
            "required_elements": {
                "learn_phase": [
                    "Learn: The Art of Innovation Storytelling",
                    "What Makes Great Presentations?",
                    "Key Elements"
                ],
                "practice_phase": [
                    "Practice: Presentation Skills Workshop",
                    "presentation-techniques",
                    "elevator-pitch"
                ],
                "apply_phase": [
                    "Apply: Create Your Innovation Showcase",
                    "presentation-builder",
                    "journey-timeline"
                ],
                "reflect_phase": [
                    "Reflect: Your Innovation Journey Complete",
                    "reflection-questions",
                    "innovation-superpowers"
                ]
            },
            "session_data": ["designThinking_presentation"],
            "expected_outputs": ["presentation structure", "innovation story", "journey summary"]
        }
    ],
    "components": [
        {
            "name": "progress_dashboard",
            "template": "templates/group_learning/design_thinking/components/progress_dashboard.html",
            "required_elements": [
                "dt-progress-dashboard",
                "mission-progress-card",
                "achievements-grid",
                "learning-stats"
            ]
        }
    ]
}

class DesignThinkingFlowTester:
    """Test runner for Design Thinking game flow validation"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.base_dir = BASE_DIR
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "mission_results": {},
            "component_results": {},
            "errors": []
        }
        
    def log(self, message, level="INFO"):
        """Log messages with optional verbosity"""
        if self.verbose or level == "ERROR":
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def test_file_exists(self, file_path):
        """Test if a template file exists"""
        full_path = self.base_dir / file_path
        if full_path.exists():
            self.log(f"✅ File exists: {file_path}")
            return True
        else:
            self.log(f"❌ File missing: {file_path}", "ERROR")
            return False
    
    def test_template_content(self, file_path, required_elements):
        """Test if template contains required LPAR elements"""
        full_path = self.base_dir / file_path
        if not full_path.exists():
            return False, f"Template file not found: {file_path}"
            
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            return False, f"Could not read template: {e}"
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            return False, f"Missing elements: {missing_elements}"
        
        return True, "All required elements found"
    
    def test_lpar_structure(self, mission):
        """Test that mission has complete Learn-Practice-Apply-Reflect structure"""
        mission_name = mission["name"]
        template_path = mission["template"]
        
        self.log(f"\n🧪 Testing {mission['title']} LPAR structure...")
        
        # Test file existence
        if not self.test_file_exists(template_path):
            return False, f"Template file missing for {mission_name}"
        
        # Test each LPAR phase
        phase_results = {}
        overall_success = True
        
        for phase, elements in mission["required_elements"].items():
            success, message = self.test_template_content(template_path, elements)
            phase_results[phase] = {"success": success, "message": message}
            
            if success:
                self.log(f"  ✅ {phase.replace('_', ' ').title()}: {message}")
            else:
                self.log(f"  ❌ {phase.replace('_', ' ').title()}: {message}", "ERROR")
                overall_success = False
        
        return overall_success, phase_results
    
    def test_data_flow(self, mission):
        """Test that mission properly handles session data flow"""
        mission_name = mission["name"]
        template_path = mission["template"]
        session_data_keys = mission.get("session_data", [])
        
        if not session_data_keys:
            return True, "No session data requirements"
        
        full_path = self.base_dir / template_path
        if not full_path.exists():
            return False, "Template file not found"
        
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            return False, f"Could not read template: {e}"
        
        # Check for session storage usage
        data_flow_indicators = [
            "sessionStorage.getItem",
            "sessionStorage.setItem", 
            "loadSaved",
            "saveTo"
        ]
        
        has_data_flow = any(indicator in content for indicator in data_flow_indicators)
        
        if has_data_flow:
            return True, "Data flow mechanisms found"
        else:
            return False, "No data flow mechanisms detected"
    
    def test_javascript_functionality(self, mission):
        """Test that mission includes proper JavaScript functionality"""
        template_path = mission["template"]
        full_path = self.base_dir / template_path
        
        if not full_path.exists():
            return False, "Template file not found"
        
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            return False, f"Could not read template: {e}"
        
        # Check for essential JavaScript features
        js_features = [
            "addEventListener",
            "function",
            "document.getElementById",
            "classList",
        ]
        
        found_features = [feature for feature in js_features if feature in content]
        
        if len(found_features) >= 3:
            return True, f"Interactive features found: {found_features}"
        else:
            return False, f"Insufficient interactivity. Found: {found_features}"
    
    def test_accessibility_features(self, mission):
        """Test that mission includes accessibility features"""
        template_path = mission["template"]
        full_path = self.base_dir / template_path
        
        if not full_path.exists():
            return False, "Template file not found"
        
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            return False, f"Could not read template: {e}"
        
        # Check for accessibility features
        a11y_features = [
            'aria-label',
            'aria-describedby',
            'role=',
            'alt=',
            'for=',  # label for inputs
            'aria-live'
        ]
        
        found_features = [feature for feature in a11y_features if feature in content]
        
        if len(found_features) >= 2:
            return True, f"Accessibility features found: {found_features}"
        else:
            return False, f"Limited accessibility. Found: {found_features}"
    
    def test_component(self, component):
        """Test component functionality"""
        component_name = component["name"]
        template_path = component["template"]
        required_elements = component["required_elements"]
        
        self.log(f"\n🧩 Testing {component_name} component...")
        
        # Test file existence
        if not self.test_file_exists(template_path):
            return False, f"Component file missing: {component_name}"
        
        # Test required elements
        success, message = self.test_template_content(template_path, required_elements)
        
        if success:
            self.log(f"  ✅ Component elements: {message}")
        else:
            self.log(f"  ❌ Component elements: {message}", "ERROR")
        
        return success, message
    
    def test_mission(self, mission):
        """Run comprehensive tests for a single mission"""
        mission_name = mission["name"]
        results = {"tests": {}, "overall_success": True}
        
        # Test LPAR structure
        lpar_success, lpar_results = self.test_lpar_structure(mission)
        results["tests"]["lpar_structure"] = {"success": lpar_success, "details": lpar_results}
        
        # Test data flow
        data_flow_success, data_flow_message = self.test_data_flow(mission)
        results["tests"]["data_flow"] = {"success": data_flow_success, "message": data_flow_message}
        
        # Test JavaScript functionality
        js_success, js_message = self.test_javascript_functionality(mission)
        results["tests"]["javascript"] = {"success": js_success, "message": js_message}
        
        # Test accessibility
        a11y_success, a11y_message = self.test_accessibility_features(mission)
        results["tests"]["accessibility"] = {"success": a11y_success, "message": a11y_message}
        
        # Calculate overall success
        test_results = [lpar_success, data_flow_success, js_success, a11y_success]
        results["overall_success"] = all(test_results)
        results["passed_tests"] = sum(test_results)
        results["total_tests"] = len(test_results)
        
        return results
    
    def run_all_tests(self, specific_mission=None):
        """Run all tests for the Design Thinking game flow"""
        self.log("🚀 Starting Design Thinking Game Flow Tests\n")
        
        # Test missions
        missions_to_test = DESIGN_THINKING_FLOW_TEST["missions"]
        if specific_mission:
            missions_to_test = [m for m in missions_to_test if m["name"] == specific_mission]
            if not missions_to_test:
                self.log(f"❌ Mission '{specific_mission}' not found", "ERROR")
                return False
        
        for mission in missions_to_test:
            mission_results = self.test_mission(mission)
            self.results["mission_results"][mission["name"]] = mission_results
            
            self.results["total_tests"] += mission_results["total_tests"]
            self.results["passed_tests"] += mission_results["passed_tests"]
            self.results["failed_tests"] += (mission_results["total_tests"] - mission_results["passed_tests"])
        
        # Test components
        if not specific_mission:  # Only test components if testing all missions
            for component in DESIGN_THINKING_FLOW_TEST["components"]:
                component_success, component_message = self.test_component(component)
                self.results["component_results"][component["name"]] = {
                    "success": component_success,
                    "message": component_message
                }
                
                self.results["total_tests"] += 1
                if component_success:
                    self.results["passed_tests"] += 1
                else:
                    self.results["failed_tests"] += 1
        
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate final test report"""
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"\n{'='*60}")
        self.log(f"🏁 DESIGN THINKING GAME FLOW TEST RESULTS")
        self.log(f"{'='*60}")
        self.log(f"Total Tests: {total}")
        self.log(f"Passed: {passed} ✅")
        self.log(f"Failed: {failed} ❌")
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        # Mission breakdown
        self.log(f"\n📋 MISSION RESULTS:")
        for mission_name, results in self.results["mission_results"].items():
            status = "✅" if results["overall_success"] else "❌"
            self.log(f"  {status} {mission_name.title()}: {results['passed_tests']}/{results['total_tests']} tests passed")
        
        # Component breakdown  
        if self.results["component_results"]:
            self.log(f"\n🧩 COMPONENT RESULTS:")
            for component_name, results in self.results["component_results"].items():
                status = "✅" if results["success"] else "❌"
                self.log(f"  {status} {component_name}: {results['message']}")
        
        # Overall assessment
        self.log(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 90:
            self.log("🌟 EXCELLENT: Design Thinking game is ready for production!")
            self.log("   All major components are working correctly.")
        elif success_rate >= 75:
            self.log("✨ GOOD: Design Thinking game is mostly ready.")
            self.log("   Minor issues to address before production.")
        elif success_rate >= 50:
            self.log("⚠️  NEEDS WORK: Several components need attention.")
            self.log("   Significant testing and fixes required.")
        else:
            self.log("🚨 CRITICAL: Major issues detected.")
            self.log("   Substantial development work needed.")
        
        return success_rate >= 75  # Return True if game is production-ready
    
    def export_results(self, output_file="dt_test_results.json"):
        """Export detailed test results to JSON file"""
        output_path = self.base_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"\n📄 Detailed results exported to: {output_path}")

def main():
    """Main entry point for the test script"""
    parser = argparse.ArgumentParser(description="Test Design Thinking Game Flow")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--mission", "-m", help="Test specific mission only")
    parser.add_argument("--export", "-e", help="Export results to JSON file")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = DesignThinkingFlowTester(verbose=args.verbose)
    
    # Run tests
    success = tester.run_all_tests(specific_mission=args.mission)
    
    # Export results if requested
    if args.export:
        tester.export_results(args.export)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()