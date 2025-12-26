"""
Script to generate a professional PDF from the USER_GUIDE.md markdown file.
Uses reportlab for PDF generation with professional styling.
"""

import re
import os
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
except ImportError:
    print("Error: reportlab is not installed. Please install it with: pip install reportlab")
    exit(1)


class PDFGenerator:
    def __init__(self, markdown_file, output_pdf):
        self.markdown_file = Path(markdown_file)
        self.output_pdf = Path(output_pdf)
        self.story = []
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Create custom paragraph styles for the PDF"""
        
        # Title style (for main title)
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=24,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#c5cae9'),
            borderPadding=10,
            backColor=colors.HexColor('#e8eaf6')
        ))
        
        # Subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubSectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#3949ab'),
            spaceAfter=10,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        ))
        
        # Sub-subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubSubSectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#5c6bc0'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style with better formatting
        if 'BodyText' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#212121'),
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                leading=14
            ))
        else:
            # Update existing style
            self.styles['BodyText'].fontSize = 10
            self.styles['BodyText'].textColor = colors.HexColor('#212121')
            self.styles['BodyText'].spaceAfter = 6
            self.styles['BodyText'].alignment = TA_JUSTIFY
            self.styles['BodyText'].leading = 14
        
        # Code/technical style
        self.styles.add(ParagraphStyle(
            name='CodeStyle',
            parent=self.styles['Code'],
            fontSize=9,
            textColor=colors.HexColor('#d32f2f'),
            fontName='Courier',
            backColor=colors.HexColor('#f5f5f5'),
            borderWidth=1,
            borderColor=colors.HexColor('#e0e0e0'),
            borderPadding=5,
            leftIndent=20,
            rightIndent=20
        ))
        
        # List item style
        if 'ListItem' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='ListItem',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#212121'),
                spaceAfter=4,
                leftIndent=20,
                bulletIndent=10
            ))
        
    def _parse_markdown(self, content):
        """Parse markdown content and convert to reportlab elements"""
        lines = content.split('\n')
        elements = []
        i = 0
        in_code_block = False
        code_block_lines = []
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Skip empty lines (except for spacing)
            if not line and not in_code_block:
                if elements and not isinstance(elements[-1], Spacer):
                    elements.append(Spacer(1, 6))
                i += 1
                continue
            
            # Code blocks
            if line.startswith('```'):
                if in_code_block:
                    # End of code block
                    code_text = '\n'.join(code_block_lines)
                    elements.append(Paragraph(f'<font face="Courier" size="9" color="#d32f2f">{self._escape_html(code_text)}</font>', 
                                             self.styles['CodeStyle']))
                    code_block_lines = []
                    in_code_block = False
                    elements.append(Spacer(1, 10))
                else:
                    in_code_block = True
                i += 1
                continue
            
            if in_code_block:
                code_block_lines.append(line)
                i += 1
                continue
            
            # Headings
            if line.startswith('# '):
                text = line[2:].strip()
                elements.append(Spacer(1, 20))
                elements.append(Paragraph(self._escape_html(text), self.styles['SectionHeading']))
                elements.append(Spacer(1, 10))
            elif line.startswith('## '):
                text = line[3:].strip()
                elements.append(Spacer(1, 16))
                elements.append(Paragraph(self._escape_html(text), self.styles['SubSectionHeading']))
                elements.append(Spacer(1, 8))
            elif line.startswith('### '):
                text = line[4:].strip()
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(self._escape_html(text), self.styles['SubSubSectionHeading']))
                elements.append(Spacer(1, 6))
            elif line.startswith('#### '):
                text = line[5:].strip()
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(f'<b>{self._escape_html(text)}</b>', self.styles['BodyText']))
                elements.append(Spacer(1, 6))
            
            # Horizontal rules
            elif line.strip() == '---' or line.strip() == '***':
                elements.append(Spacer(1, 10))
                # Create a simple line using a table
                hr_table = Table([['']], colWidths=[7*inch], rowHeights=[0.02*inch])
                hr_table.setStyle(TableStyle([
                    ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#bdbdbd'))
                ]))
                elements.append(hr_table)
                elements.append(Spacer(1, 10))
            
            # Lists
            elif line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                elements.append(Paragraph(f'• {self._process_text(text)}', self.styles['ListItem']))
            elif re.match(r'^\d+\.\s', line):
                match = re.match(r'^(\d+)\.\s(.*)', line)
                if match:
                    num, text = match.groups()
                    elements.append(Paragraph(f'{num}. {self._process_text(text)}', self.styles['ListItem']))
            
            # Inline code
            elif '`' in line:
                processed = self._process_inline_code(line)
                elements.append(Paragraph(processed, self.styles['BodyText']))
                elements.append(Spacer(1, 6))
            
            # Bold and italic
            elif '**' in line or '*' in line:
                processed = self._process_formatting(line)
                elements.append(Paragraph(processed, self.styles['BodyText']))
                elements.append(Spacer(1, 6))
            
            # Regular paragraph
            else:
                if line.strip():
                    processed = self._process_text(line)
                    elements.append(Paragraph(processed, self.styles['BodyText']))
                    elements.append(Spacer(1, 6))
            
            i += 1
        
        return elements
    
    def _escape_html(self, text):
        """Escape HTML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    def _process_text(self, text):
        """Process text for formatting (bold, italic, inline code, links)"""
        text = self._escape_html(text)
        
        # Process inline code `code`
        text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9" color="#d32f2f">\1</font>', text)
        
        # Process bold **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
        
        # Process italic *text* (but not if it's part of **text**)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
        
        # Process links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<font color="#1976d2"><u>\1</u></font>', text)
        
        return text
    
    def _process_inline_code(self, text):
        """Process inline code blocks"""
        return self._process_text(text)
    
    def _process_formatting(self, text):
        """Process bold and italic formatting"""
        return self._process_text(text)
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        # Save the current state
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.HexColor('#1a237e'))
        canvas_obj.drawString(inch, letter[1] - 0.5*inch, "DMS Tool - User Guide")
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawCentredString(letter[0]/2, 0.5*inch, f"Page {page_num}")
        
        # Draw a line above footer
        canvas_obj.setStrokeColor(colors.HexColor('#bdbdbd'))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(inch, 0.7*inch, letter[0] - inch, 0.7*inch)
        
        # Restore the state
        canvas_obj.restoreState()
    
    def generate(self):
        """Generate the PDF document"""
        if not self.markdown_file.exists():
            print(f"Error: Markdown file not found: {self.markdown_file}")
            return False
        
        print(f"Reading markdown file: {self.markdown_file}")
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse markdown and get elements
        print("Parsing markdown content...")
        elements = self._parse_markdown(content)
        
        # Create PDF document
        print(f"Generating PDF: {self.output_pdf}")
        doc = SimpleDocTemplate(
            str(self.output_pdf),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Add title page
        title_elements = []
        title_elements.append(Spacer(1, 2*inch))
        title_elements.append(Paragraph("DMS Tool", self.styles['CustomTitle']))
        title_elements.append(Spacer(1, 0.5*inch))
        title_elements.append(Paragraph("User Guide", self.styles['CustomTitle']))
        title_elements.append(Spacer(1, 1*inch))
        title_elements.append(Paragraph("Comprehensive Guide to Using the Data Management System", 
                                        ParagraphStyle(
                                            name='Subtitle',
                                            parent=self.styles['Normal'],
                                            fontSize=14,
                                            textColor=colors.HexColor('#546e7a'),
                                            alignment=TA_CENTER
                                        )))
        title_elements.append(Spacer(1, 2*inch))
        title_elements.append(Paragraph(f"<i>Version 4.0.0</i>", 
                                        ParagraphStyle(
                                            name='Version',
                                            parent=self.styles['Normal'],
                                            fontSize=12,
                                            alignment=TA_CENTER
                                        )))
        title_elements.append(PageBreak())
        
        # Build the document
        doc.build(title_elements + elements, onFirstPage=self._add_header_footer, 
                 onLaterPages=self._add_header_footer)
        
        print(f"PDF generated successfully: {self.output_pdf}")
        print(f"File size: {self.output_pdf.stat().st_size / 1024:.2f} KB")
        return True


def main():
    """Main function"""
    script_dir = Path(__file__).parent
    markdown_file = script_dir / "USER_GUIDE.md"
    output_pdf = script_dir / "DMS_Tool_User_Guide.pdf"
    
    print("=" * 60)
    print("DMS Tool User Guide PDF Generator")
    print("=" * 60)
    print()
    
    generator = PDFGenerator(markdown_file, output_pdf)
    success = generator.generate()
    
    if success:
        print()
        print("=" * 60)
        print("SUCCESS!")
        print(f"PDF generated at: {output_pdf.absolute()}")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("FAILED to generate PDF")
        print("=" * 60)


if __name__ == "__main__":
    main()

