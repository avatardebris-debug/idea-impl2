"""Formatter module for output format converters."""

import os
from datetime import datetime
from typing import Optional, List
from email_tool.models import Email


class Formatter:
    """
    Converts emails to different output formats.
    
    Supported formats:
    - .eml: Raw email content
    - .md: Markdown summary with headers, body, and attachment list
    - .pdf: Email converted to PDF using fpdf
    """
    
    def __init__(self, email: Email):
        """
        Initialize the formatter with an email.
        
        Args:
            email: The email object to format.
        """
        self.email = email
    
    def to_eml(self) -> str:
        """
        Export email as raw .eml content.
        
        Returns:
            Raw email content as string.
        """
        lines = []
        
        # From
        if self.email.from_addr:
            lines.append(f"From: {self.email.from_addr}")
        else:
            lines.append("From: Unknown")
        
        # To
        if self.email.to_addrs:
            to_addr = ", ".join(self.email.to_addrs)
            lines.append(f"To: {to_addr}")
        
        # Subject
        if self.email.subject:
            lines.append(f"Subject: {self.email.subject}")
        
        # Date
        if self.email.date:
            lines.append(f"Date: {self.email.date.strftime('%a, %d %b %Y %H:%M:%S %z')}")
        
        # Raw headers
        for header, value in self.email.raw_headers.items():
            lines.append(f"{header}: {value}")
        
        # Body separator
        lines.append("")
        
        # Body
        if self.email.body_plain:
            lines.append(self.email.body_plain)
        elif self.email.body_html:
            # Strip HTML tags for plain text representation
            lines.append(self._strip_html(self.email.body_html))
        
        # Attachments
        if self.email.attachments:
            lines.append("")
            lines.append("Attachments:")
            for attachment in self.email.attachments:
                lines.append(f"  - {attachment}")
        
        return "\n".join(lines)
    
    def to_markdown(self) -> str:
        """
        Create markdown summary of email.
        
        Returns:
            Markdown formatted email summary.
        """
        lines = []
        
        # Title
        lines.append(f"# Email: {self.email.subject or 'No Subject'}")
        lines.append("")
        
        # Metadata
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **From:** {self.email.from_addr or 'Unknown'}")
        
        if self.email.to_addrs:
            to_addr = ", ".join(self.email.to_addrs)
            lines.append(f"- **To:** {to_addr}")
        
        if self.email.date:
            lines.append(f"- **Date:** {self.email.date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        lines.append("")
        
        # Body
        lines.append("## Body")
        lines.append("")
        
        if self.email.body_plain:
            lines.append(self.email.body_plain)
        elif self.email.body_html:
            # Convert HTML to markdown-like format
            lines.append(self._html_to_markdown(self.email.body_html))
        else:
            lines.append("*No body content*")
        
        lines.append("")
        
        # Attachments
        if self.email.attachments:
            lines.append("## Attachments")
            lines.append("")
            for attachment in self.email.attachments:
                lines.append(f"- {attachment}")
            lines.append("")
        
        # Raw headers
        if self.email.raw_headers:
            lines.append("## Raw Headers")
            lines.append("")
            for header, value in self.email.raw_headers.items():
                lines.append(f"- `{header}`: {value}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_pdf(self, output_path: str, title: Optional[str] = None) -> bool:
        """
        Convert email to PDF format.
        
        Args:
            output_path: Path where PDF will be saved.
            title: Optional title for the PDF (defaults to email subject).
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            from fpdf import FPDF
            
            # Use subject as title if not provided
            pdf_title = title or (self.email.subject or "Email")
            
            # Create PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, pdf_title, ln=True, align="C")
            pdf.ln(10)
            
            # Add metadata
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 8, f"From: {self.email.from_addr or 'Unknown'}", ln=True)
            
            if self.email.to_addrs:
                to_addr = ", ".join(self.email.to_addrs)
                pdf.cell(0, 8, f"To: {to_addr}", ln=True)
            
            if self.email.date:
                pdf.cell(0, 8, f"Date: {self.email.date.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            
            pdf.ln(5)
            
            # Add body
            pdf.set_font("Helvetica", "", 10)
            body_text = self.email.body_plain or ""
            
            if not body_text and self.email.body_html:
                body_text = self._strip_html(self.email.body_html)
            
            if body_text:
                # Split into lines and add with proper wrapping
                lines = body_text.split("\n")
                for line in lines:
                    pdf.multi_cell(0, 5, line)
            
            # Add attachments section
            if self.email.attachments:
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 8, "Attachments:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                
                for attachment in self.email.attachments:
                    pdf.cell(0, 5, f"- {attachment}", ln=True)
            
            # Save PDF
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            pdf.output(output_path)
            
            return True
            
        except ImportError:
            # fpdf not installed
            return False
        except Exception:
            return False
    
    def _strip_html(self, html_content: str) -> str:
        """
        Strip HTML tags from HTML content.
        
        Args:
            html_content: HTML string.
        
        Returns:
            Plain text version.
        """
        import re
        import html as html_module
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities using html.unescape
        text = html_module.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to simple markdown-like format.
        
        Args:
            html: HTML string.
        
        Returns:
            Markdown-formatted text.
        """
        import re
        
        text = self._strip_html(html)
        
        # Convert paragraphs
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text
    
    def format(self, output_format: str, output_path: Optional[str] = None) -> str:
        """
        Format email to specified output format.
        
        Args:
            output_format: Output format ('eml', 'md', 'pdf').
            output_path: Optional path for PDF format.
        
        Returns:
            Formatted content (or path for PDF).
        """
        if output_format == "eml":
            return self.to_eml()
        elif output_format == "md":
            return self.to_markdown()
        elif output_format == "pdf":
            if not output_path:
                raise ValueError("output_path required for PDF format")
            success = self.to_pdf(output_path)
            if success:
                return output_path
            else:
                raise RuntimeError("Failed to create PDF")
        else:
            raise ValueError(f"Unknown output format: {output_format}")


class BatchFormatter:
    """
    Formats multiple emails to different output formats.
    """
    
    def __init__(self, emails: List[Email]):
        """
        Initialize batch formatter.
        
        Args:
            emails: List of email objects to format.
        """
        self.emails = emails
    
    def format_all(
        self,
        output_format: str,
        base_path: str,
        filename_template: str = "{{subject_sanitized}}.{ext}"
    ) -> List[str]:
        """
        Format all emails to specified output format.
        
        Args:
            output_format: Output format ('eml', 'md', 'pdf').
            base_path: Base directory for output files.
            filename_template: Template for filenames.
        
        Returns:
            List of output file paths.
        """
        from email_tool.path_builder import PathBuilder
        import re
        
        output_paths = []
        ext = output_format
        
        for email in self.emails:
            formatter = Formatter(email)
            
            # Build filename from template
            path_builder = PathBuilder()
            
            # Replace template variables
            def replace_var(match):
                var_name = match.group(1)
                if var_name == "subject_sanitized":
                    return path_builder._sanitize_subject(email.subject)
                elif var_name == "from_domain":
                    from_addr = email.from_addr or ""
                    if "@" in from_addr:
                        domain = from_addr.split("@")[-1]
                        return path_builder._sanitize_filename(domain)
                    return from_addr
                elif var_name == "year":
                    if email.date:
                        return email.date.strftime("%Y")
                    return "unknown"
                elif var_name == "month":
                    if email.date:
                        return email.date.strftime("%m")
                    return "unknown"
                elif var_name == "day":
                    if email.date:
                        return email.date.strftime("%d")
                    return "unknown"
                elif var_name == "ext":
                    return ext
                return match.group(0)
            
            # Support both {{var}} and {var} syntax
            filename = re.sub(r"\{\{(\w+)\}\}", replace_var, filename_template)
            filename = re.sub(r"\{(\w+)\}", replace_var, filename)
            
            # Full path
            output_path = os.path.join(base_path, filename)
            
            # Format email
            if output_format == "pdf":
                formatter.to_pdf(output_path)
            else:
                content = formatter.format(output_format)
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            output_paths.append(output_path)
        
        return output_paths
