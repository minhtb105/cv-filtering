"""Quick test of refactored Clean Architecture modules"""
import sys


def test_post_processor():
    """Test PostProcessor module"""
    print("\n" + "="*60)
    print("Testing PostProcessor")
    print("="*60)
    
    try:
        from src.processing.post_processor import PostProcessor
        pp = PostProcessor()
        print("✓ PostProcessor imported successfully")
        
        # Test date normalization
        tests = [
            ("2024-01", "2024-01-01"),
            ("2024-01-15", "2024-01-15"),
            ("January 2024", "2024-01-01"),
            ("Jan 2024", "2024-01-01"),
        ]
        
        for input_date, expected in tests:
            result = pp.normalize_date(input_date)
            status = "✓" if result == expected else "✗"
            print(f"{status} normalize_date('{input_date}') = '{result}' (expected: '{expected}')")
            assert result == expected, f"Mismatch!"
        
        print("\n✓ All PostProcessor tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ PostProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator():
    """Test HRExtractorAgent orchestrator"""
    print("\n" + "="*60)
    print("Testing HRExtractorAgent Orchestrator")
    print("="*60)
    
    try:
        from src.extraction.hr_extractor_agent import HRExtractorAgent, ExtractionConfig
        config = ExtractionConfig(use_llm=False)
        orchestrator = HRExtractorAgent(config)
        print("✓ HRExtractorAgent orchestrator initialized")
        
        # Test with empty input
        result = orchestrator.extract_cv("")
        assert result["status"] == "error", "Should return error for empty input"
        print("✓ Handles empty input correctly (status: error)")
        
        # Test extract_ordered_text pass-through
        sample_text = "# EXPERIENCE\nSample job 2023-01"
        result = orchestrator.extract_ordered_text(sample_text)
        assert result == sample_text, "Should pass through text unchanged"
        print("✓ extract_ordered_text() works (pass-through)")
        
        print("\n✓ All Orchestrator tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    results = []
    
    results.append(test_post_processor())
    results.append(test_orchestrator())
    
    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)
    
    sys.exit(0 if all(results) else 1)
