import re
from typing import List, Union

class InstructionProcessor:
    """Handles processing and splitting of recipe instructions"""
    
    @staticmethod
    def process_instructions(raw_instructions: Union[str, list]) -> List[str]:
        """Process raw instructions and return a clean list of steps"""
        instructions = []
        
        print(f"🔧 Processing instructions of type: {type(raw_instructions)}")
        
        if isinstance(raw_instructions, str):
            # Single concatenated string - split it intelligently
            print(f"🔧 Found concatenated string instruction, splitting...")
            instructions = InstructionProcessor._split_concatenated_instructions(raw_instructions)
            
        elif isinstance(raw_instructions, list):
            for instr in raw_instructions:
                if isinstance(instr, dict):
                    text = instr.get('text', instr.get('name', str(instr)))
                else:
                    text = str(instr)
                
                if text and len(text.strip()) > 5:
                    # Check if this single instruction is actually concatenated
                    if InstructionProcessor._looks_like_concatenated_steps(text):
                        print(f"🔧 Found concatenated instruction in list, splitting...")
                        split_steps = InstructionProcessor._split_concatenated_instructions(text)
                        instructions.extend(split_steps)
                    else:
                        instructions.append(text.strip())
        
        # Clean up instructions
        cleaned_instructions = []
        for instruction in instructions:
            instruction = instruction.strip()
            if len(instruction) > 10:  # Only keep substantial instructions
                cleaned_instructions.append(instruction)
        
        return cleaned_instructions
    
    @staticmethod
    def _looks_like_concatenated_steps(text: str) -> bool:
        """Check if text looks like multiple steps concatenated together"""
        # Look for patterns that suggest multiple steps
        step_indicators = [
            'To Prep', 'To Cook', 'To Serve', 'To Finish',
            'Step 1', 'Step 2', 'Step 3',
            'Heat some', 'Next', 'Then', 'When', 'After', 'Meanwhile',
            '1.', '2.', '3.', '4.', '5.',
            'In a', 'Add the', 'Remove from'
        ]
        
        found_indicators = sum(1 for indicator in step_indicators if indicator in text)
        
        # If we find multiple step indicators or the text is very long, it's likely concatenated
        return found_indicators >= 2 or len(text) > 500
    
    @staticmethod
    def _split_concatenated_instructions(text: str) -> List[str]:
        """Split concatenated instructions into separate steps"""
        
        # Split on common patterns
        split_patterns = [
            r'\n\n+',  # Double newlines or more
            r'(?=To Prep\b)',
            r'(?=To Cook\b)', 
            r'(?=To Serve\b)',
            r'(?=To Finish\b)',
            r'(?=Next\b)',
            r'(?=Then\b)',
            r'(?=Meanwhile\b)',
            r'(?=\d+\.)',  # Numbered steps like "1.", "2."
            r'(?=Step \d+)',  # Step 1, Step 2, etc.
        ]
        
        instructions = [text]  # Start with the full text
        
        # Apply each split pattern
        for pattern in split_patterns:
            new_instructions = []
            for instruction in instructions:
                try:
                    parts = re.split(pattern, instruction)
                    new_instructions.extend([part.strip() for part in parts if part.strip()])
                except re.error:
                    # If regex fails, keep the original
                    new_instructions.append(instruction)
            instructions = new_instructions
        
        # Clean up and filter
        cleaned_instructions = []
        for instruction in instructions:
            instruction = instruction.strip()
            if len(instruction) > 20:  # Only keep substantial instructions
                cleaned_instructions.append(instruction)
        
        print(f"Split concatenated text into {len(cleaned_instructions)} instructions")
        return cleaned_instructions if cleaned_instructions else [text]
    
    @staticmethod
    def clean_instruction_text(text: str) -> str:
        """Clean up individual instruction text"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up common artifacts
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        
        return text.strip()
