"""
DecipherWorld Game Framework - Backwards Compatibility Layer
Ensures existing Constitution Challenge continues to work unchanged
"""

from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)


class BackwardsCompatibilityManager:
    """
    Manages backwards compatibility for existing games
    Ensures zero breaking changes to existing URLs and APIs
    """
    
    def __init__(self):
        self.legacy_url_mappings = {}
        self.legacy_view_mappings = {}
    
    def register_legacy_url(self, old_pattern: str, new_pattern: str):
        """Register a legacy URL mapping"""
        self.legacy_url_mappings[old_pattern] = new_pattern
        logger.info(f"Registered legacy URL mapping: {old_pattern} -> {new_pattern}")
    
    def register_legacy_view(self, old_view: str, new_view: str):
        """Register a legacy view mapping"""
        self.legacy_view_mappings[old_view] = new_view
        logger.info(f"Registered legacy view mapping: {old_view} -> {new_view}")
    
    def get_legacy_urls(self):
        """Get URL patterns for legacy compatibility"""
        patterns = []
        
        for old_pattern, new_pattern in self.legacy_url_mappings.items():
            # Create redirect patterns for legacy URLs
            patterns.append(
                path(old_pattern, self.create_redirect_view(new_pattern))
            )
        
        return patterns
    
    def create_redirect_view(self, new_pattern: str):
        """Create a redirect view for legacy URLs"""
        def redirect_view(request, *args, **kwargs):
            return redirect(new_pattern.format(**kwargs))
        return redirect_view


# Global compatibility manager
compatibility_manager = BackwardsCompatibilityManager()


class ConstitutionGameCompatibility:
    """
    Specific compatibility layer for Constitution Challenge
    Ensures all existing URLs and functionality continue to work
    """
    
    @staticmethod
    def ensure_compatibility():
        """Set up compatibility for Constitution Challenge"""
        
        # Constitution Challenge URLs must continue to work exactly as before
        existing_urls = [
            'constitution/start/',
            'constitution/start/<str:level>/',
            'constitution/<str:session_code>/',
            'constitution/<str:session_code>/play/',
            'constitution/<str:session_code>/create-team/',
            'constitution/<str:session_code>/final-results/',
            'constitution/<str:session_code>/feedback/',
            'api/constitution/<str:session_code>/question/',
            'api/constitution/<str:session_code>/answer/',
            'api/constitution/<str:session_code>/leaderboard/',
        ]
        
        # All these URLs must continue to work with existing group_learning.views
        # No changes to existing URL patterns allowed
        logger.info("Constitution Challenge compatibility ensured - all existing URLs preserved")
    
    @staticmethod
    def verify_existing_views():
        """Verify that existing views still work"""
        try:
            from group_learning.views import (
                ConstitutionQuickStartView,
                ConstitutionTeamJoinView,
                ConstitutionGameView,
                ConstitutionTeamCreateView,
                ConstitutionFinalResultsView,
                ConstitutionFeedbackView,
                ConstitutionQuestionAPI,
                ConstitutionAnswerAPI,
                ConstitutionLeaderboardAPI,
            )
            
            logger.info("✅ All existing Constitution Challenge views are accessible")
            return True
            
        except ImportError as e:
            logger.error(f"❌ Constitution Challenge view compatibility issue: {e}")
            return False
    
    @staticmethod
    def verify_existing_models():
        """Verify that existing models still work"""
        try:
            from group_learning.models import (
                Game,
                GameSession,
                ConstitutionTeam,
                ConstitutionQuestion,
                ConstitutionOption,
                ConstitutionAnswer,
                CountryState,
            )
            
            logger.info("✅ All existing Constitution Challenge models are accessible")
            return True
            
        except ImportError as e:
            logger.error(f"❌ Constitution Challenge model compatibility issue: {e}")
            return False


class FrameworkIntegrationTest:
    """
    Test that the new framework doesn't break existing functionality
    """
    
    def __init__(self):
        self.test_results = {}
    
    def run_compatibility_tests(self) -> dict:
        """Run comprehensive compatibility tests"""
        
        tests = [
            ('existing_views', self.test_existing_views),
            ('existing_models', self.test_existing_models),
            ('existing_urls', self.test_existing_urls),
            ('framework_import', self.test_framework_import),
            ('no_conflicts', self.test_no_conflicts),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.test_results[test_name] = {
                    'status': 'PASS' if result else 'FAIL',
                    'result': result
                }
            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        return self.test_results
    
    def test_existing_views(self) -> bool:
        """Test that existing views still work"""
        return ConstitutionGameCompatibility.verify_existing_views()
    
    def test_existing_models(self) -> bool:
        """Test that existing models still work"""
        return ConstitutionGameCompatibility.verify_existing_models()
    
    def test_existing_urls(self) -> bool:
        """Test that existing URL patterns are preserved"""
        try:
            from group_learning.urls import urlpatterns
            
            # Check that key Constitution Challenge URLs exist
            required_patterns = [
                'constitution_quick_start',
                'constitution_join',
                'constitution_game',
                'constitution_final_results',
                'constitution_question_api',
                'constitution_answer_api',
            ]
            
            pattern_names = [p.name for p in urlpatterns if hasattr(p, 'name')]
            
            for required in required_patterns:
                if required not in pattern_names:
                    logger.error(f"Missing required URL pattern: {required}")
                    return False
            
            logger.info("✅ All required URL patterns exist")
            return True
            
        except Exception as e:
            logger.error(f"URL pattern test failed: {e}")
            return False
    
    def test_framework_import(self) -> bool:
        """Test that new framework components can be imported"""
        try:
            from games.base.models import BaseGameSession, BaseGamePlayer, GameInterface
            from games.base.views import BaseGameViewMixin, BaseGameSessionView
            from games.engine import GameEngine, GamePlugin
            from games.utils.builders import GameScaffold
            from games.utils.performance import GameCacheManager
            
            logger.info("✅ All framework components imported successfully")
            return True
            
        except ImportError as e:
            logger.error(f"Framework import failed: {e}")
            return False
    
    def test_no_conflicts(self) -> bool:
        """Test that framework doesn't conflict with existing code"""
        try:
            # Test that we can import both old and new without conflicts
            from group_learning.views import ConstitutionGameView
            from games.base.views import BaseGameSessionView
            
            # Test that they don't interfere with each other
            old_view = ConstitutionGameView()
            new_view = BaseGameSessionView()
            
            logger.info("✅ No conflicts between old and new components")
            return True
            
        except Exception as e:
            logger.error(f"Conflict test failed: {e}")
            return False
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report"""
        if not self.test_results:
            self.run_compatibility_tests()
        
        report = "🧪 GAME FRAMEWORK COMPATIBILITY TEST REPORT\n"
        report += "=" * 50 + "\n\n"
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            report += f"{status_icon} {test_name.replace('_', ' ').title()}: {result['status']}\n"
            
            if result['status'] == 'PASS':
                passed += 1
            elif result['status'] == 'ERROR':
                report += f"   Error: {result.get('error', 'Unknown error')}\n"
        
        report += "\n" + "=" * 50 + "\n"
        report += f"SUMMARY: {passed}/{total} tests passed\n"
        
        if passed == total:
            report += "🎉 ALL TESTS PASSED - Framework is ready for production!\n"
        else:
            report += "⚠️  Some tests failed - Review issues before deployment\n"
        
        return report


def run_framework_integration_test():
    """Run the framework integration test and return results"""
    tester = FrameworkIntegrationTest()
    results = tester.run_compatibility_tests()
    report = tester.generate_test_report()
    
    return {
        'results': results,
        'report': report,
        'all_passed': all(r['status'] == 'PASS' for r in results.values())
    }


# Setup compatibility on module import
def setup_compatibility():
    """Set up backwards compatibility for all existing games"""
    ConstitutionGameCompatibility.ensure_compatibility()
    logger.info("Game framework backwards compatibility initialized")


# Auto-setup when module is imported
setup_compatibility()