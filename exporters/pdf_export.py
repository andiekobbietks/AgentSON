"""
AgentSON PDF Exporter - Export .agentson files to formatted PDF using PyLaTeX.
"""

import json
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# PyLaTeX imports
from pylatex import Document, Section, Subsection, Command, Package
from pylatex.basic import TextColor, NewLine, HFill, LineBreak
from pylatex.utils import NoEscape, bold, italic, verbatim


def find_or_install_latex() -> Optional[str]:
    """Find an existing LaTeX compiler or auto-install one."""
    # Check for existing compilers in PATH
    for compiler in ['pdflatex', 'xelatex', 'lualatex', 'latexmk']:
        path = shutil.which(compiler)
        if path:
            print(f"Found LaTeX compiler: {compiler} at {path}")
            return compiler
    
    # Check common MiKTeX installation paths on Windows
    import platform
    if platform.system() == 'Windows':
        common_paths = [
            Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64",
            Path("C:/Program Files/MiKTeX/miktex/bin/x64"),
            Path("C:/Program Files (x86)/MiKTeX/miktex/bin/x64"),
            Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin",
        ]
        for path in common_paths:
            pdflatex = path / "pdflatex.exe"
            if pdflatex.exists():
                # Add to PATH for this session
                os.environ['PATH'] = str(path) + ';' + os.environ['PATH']
                print(f"Found LaTeX compiler: pdflatex at {pdflatex}")
                return 'pdflatex'
    
    print("No LaTeX compiler found. Attempting auto-install...")
    
    # Try winget (Windows)
    if shutil.which('winget'):
        try:
            print("Installing MiKTeX via winget...")
            result = subprocess.run(
                ['winget', 'install', 'MiKTeX.MiKTeX', '--accept-source-agreements', '--accept-package-agreements'],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                # Refresh PATH
                os.environ['PATH'] = subprocess.check_output(
                    ['powershell', '-Command', '[Environment]::GetEnvironmentVariable("PATH","Machine")'],
                    text=True
                ).strip() + ';' + os.environ['PATH']
                
                # Check again
                path = shutil.which('pdflatex')
                if path:
                    print(f"MiKTeX installed successfully! pdflatex at: {path}")
                    return 'pdflatex'
        except Exception as e:
            print(f"Winget install failed: {e}")
    
    # Try choco (Windows)
    if shutil.which('choco'):
        try:
            print("Installing MiKTeX via Chocolatey...")
            result = subprocess.run(
                ['choco', 'install', 'miktex', '-y'],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                os.environ['PATH'] = subprocess.check_output(
                    ['powershell', '-Command', '[Environment]::GetEnvironmentVariable("PATH","Machine")'],
                    text=True
                ).strip() + ';' + os.environ['PATH']
                
                path = shutil.which('pdflatex')
                if path:
                    print(f"MiKTeX installed successfully! pdflatex at: {path}")
                    return 'pdflatex'
        except Exception as e:
            print(f"Chocolatey install failed: {e}")
    
    # Try apt (Linux/WSL)
    if shutil.which('apt'):
        try:
            print("Installing texlive via apt...")
            result = subprocess.run(
                ['sudo', 'apt-get', 'install', '-y', 'texlive-latex-recommended', 'texlive-fonts-recommended'],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                path = shutil.which('pdflatex')
                if path:
                    print(f"texlive installed successfully! pdflatex at: {path}")
                    return 'pdflatex'
        except Exception as e:
            print(f"apt install failed: {e}")
    
    # Try brew (macOS)
    if shutil.which('brew'):
        try:
            print("Installing mactex via brew...")
            result = subprocess.run(
                ['brew', 'install', '--cask', 'mactex'],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                path = shutil.which('pdflatex')
                if path:
                    print(f"MacTeX installed successfully! pdflatex at: {path}")
                    return 'pdflatex'
        except Exception as e:
            print(f"brew install failed: {e}")
    
    print("Auto-install failed. Please install manually:")
    print("  Windows: winget install MiKTeX.MiKTeX")
    print("  Linux:   sudo apt install texlive-latex-recommended")
    print("  macOS:   brew install --cask mactex")
    return None


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters with simplified approach."""
    if not text:
        return ""
    
    text = str(text)
    
    # Remove all non-ASCII characters first
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # Handle LaTeX commands before escaping backslashes
    # Replace \newline with \par (vertical space)
    text = text.replace('\\newline', '\\par')
    text = text.replace('\\newline%', '\\par%')
    # Also handle actual newline characters
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    
    # Handle backslashes (most important - prevents double-escaping)
    text = text.replace('\\', '\\textbackslash{}')
    
    # Handle braces
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    
    # Handle dollar signs (critical - causes math mode errors)
    text = text.replace('$', '\\$')
    
    # Handle other special chars
    text = text.replace('#', '\\#')
    text = text.replace('_', '\\_')
    text = text.replace('%', '\\%')
    text = text.replace('&', '\\&')
    text = text.replace('^', '\\^{}')
    text = text.replace('~', '\\~{}')
    text = text.replace("'", "''")
    
    # Clean up any double-escaping that might have occurred
    text = text.replace('\\textbackslash{}\\textbackslash{}', '\\textbackslash{}')
    
    # Handle newline commands - replace with par or remove
    text = text.replace('\\newline', '\\par')
    text = text.replace('\\newline%', '\\par%')
    
    return text


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters with ellipsis."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


class AgentSONPDFExporter:
    """Export AgentSON files to formatted PDF."""
    
    def __init__(self):
        self.doc = None
        self.entry_colors = {
            'user': 'blue',
            'assistant': 'black',
            'tool': 'darkgray',
            'error': 'red',
            'system': 'gray',
            'result': 'green',
            'thought': 'violet',
            'thought_call': 'violet',
            'thought_result': 'violet',
        }
    
    def export(self, input_path: str, output_path: str = None, 
               max_text_length: int = 300, include_analytics: bool = True) -> str:
        """Export an .agentson file to PDF."""
        
        # Load the .agentson file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create output path
        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.pdf'))
        
        # Create document
        self.doc = Document()
        
        # Set document class
        self.doc.documentclass = Command(
            'documentclass',
            options=['11pt', 'a4paper'],
            arguments=['article']
        )
        
        # Add packages
        self.doc.packages.append(Package('geometry', options=['margin=1in']))
        self.doc.packages.append(Package('xcolor', options=['table']))
        self.doc.packages.append(Package('listings'))
        self.doc.packages.append(Package('hyperref'))
        self.doc.packages.append(Package('fancyhdr'))
        self.doc.packages.append(Package('pgfplots'))
        self.doc.packages.append(Package('tikz'))
        self.doc.packages.append(Package('courier'))  # Monospace font for code
        self.doc.packages.append(Package('setspace'))  # Line spacing
        self.doc.preamble.append(NoEscape(r'\usepgfplotslibrary{statistics}'))
        self.doc.preamble.append(NoEscape(r'\pgfplotsset{compat=1.18}'))
        self.doc.preamble.append(NoEscape(r'\onehalfspacing'))  # 1.5 line spacing
        # Configure code listings style
        self.doc.preamble.append(NoEscape(r'''
\lstset{
  basicstyle=\ttfamily\small,
  backgroundcolor=\color{gray!10},
  frame=single,
  breaklines=true,
  breakatwhitespace=true,
  columns=flexible,
  keepspaces=true,
  showstringspaces=false,
  numbers=none,
  keywordstyle=\color{blue},
  commentstyle=\color{green!60!black},
  stringstyle=\color{red!80!black},
  tabsize=2
}
'''))
        
        # Add header/footer
        self.doc.preamble.append(Command('pagestyle', 'fancy'))
        self.doc.preamble.append(Command('fancyhead', arguments=[NoEscape(r'\leftmark')]))
        self.doc.preamble.append(Command('fancyfoot', arguments=[NoEscape(r'\thepage')]))
        
        # Title
        title = self._get_session_title(data)
        self.doc.preamble.append(Command('title', escape_latex(title)))
        self.doc.preamble.append(Command('author', escape_latex('AgentSON')))
        self.doc.preamble.append(Command('date', escape_latex(datetime.now().strftime('%Y-%m-%d %H:%M'))))
        
        # Build document
        self.doc.append(NoEscape(r'\maketitle'))
        
        # Metadata section
        self._add_metadata_section(data)
        
        # Analytics section
        if include_analytics:
            self._add_analytics_section(data)
        
        # Conversation section
        self._add_conversation_section(data, max_text_length, max_entries=100)
        
        # Try to find or install LaTeX compiler
        compiler = find_or_install_latex()
        
        # Generate PDF
        try:
            if compiler:
                # Save .tex first - pass filename WITHOUT .tex extension (PyLaTeX adds it)
                output_stem = Path(output_path).stem
                if output_stem.endswith('.pdf'):
                    output_stem = output_stem[:-4]
                # PyLaTeX's generate_tex adds .tex, so pass without extension
                tex_base = str(Path(output_path).parent / output_stem)
                tex_path = tex_base + '.tex'
                self.doc.generate_tex(tex_base)
                
                # Run pdflatex with batch mode (no user interaction)
                import subprocess
                import os
                
                # Save current directory and change to output directory
                original_dir = os.getcwd()
                os.chdir(str(Path(output_path).parent))
                
                try:
                    result = subprocess.run(
                        [compiler, '-interaction=batchmode', str(Path(tex_path).name)],
                        capture_output=True, text=True, timeout=300
                    )
                    
                    # Check if PDF was generated (even with errors, pdflatex may produce PDF)
                    generated_pdf = f"{output_stem}.pdf"
                    if Path(generated_pdf).exists():
                        # Rename to desired output path if different
                        if generated_pdf != Path(output_path).name:
                            Path(generated_pdf).rename(Path(output_path).name)
                        print(f"PDF exported to: {output_path}")
                        # Clean up .tex file
                        Path(tex_path).unlink(missing_ok=True)
                        return output_path
                    else:
                        # Check log file for errors
                        log_file = f"{output_stem}.log"
                        if Path(log_file).exists():
                            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                log_content = f.read()
                            # Find error messages
                            import re
                            errors = re.findall(r'! (.+?)\n', log_content)
                            if errors:
                                print(f"PDF compilation errors: {errors[0][:200]}")
                        print(f"PDF compilation failed. TeX file saved to: {tex_path}")
                        return tex_path
                finally:
                    os.chdir(original_dir)
            else:
                raise Exception("No LaTeX compiler available")
        except subprocess.TimeoutExpired:
            print(f"PDF compilation timed out. TeX file saved to: {tex_path}")
            return tex_path
        except Exception as e:
            # Fallback: save as .tex file
            output_stem = Path(output_path).stem
            if output_stem.endswith('.pdf'):
                output_stem = output_stem[:-4]
            tex_base = str(Path(output_path).parent / output_stem)
            tex_path = tex_base + '.tex'
            self.doc.generate_tex(tex_base)
            print(f"PDF generation failed ({e}). TeX file saved to: {tex_path}")
            return tex_path
    
    def _get_session_title(self, data: dict) -> str:
        """Generate session title from metadata."""
        session_id = data.get('id', 'Unknown')
        if len(session_id) > 20:
            session_id = session_id[:20] + '...'
        
        tool = data.get('tool', {})
        if isinstance(tool, dict):
            tool_name = tool.get('name', 'Unknown')
        else:
            tool_name = str(tool)
        
        return f"AgentSON Session: {tool_name} ({session_id})"
    
    def _add_metadata_section(self, data: dict):
        """Add metadata section to document."""
        with self.doc.create(Section('Session Metadata')):
            # Session info table
            metadata = [
                ("Session ID", data.get('id', 'N/A')),
                ("Tool", data.get('tool', {}).get('name', 'N/A') if isinstance(data.get('tool'), dict) else 'N/A'),
                ("Agent", data.get('agent', {}).get('name', 'N/A') if isinstance(data.get('agent'), dict) else 'N/A'),
                ("Started", data.get('started_at', 'N/A')),
                ("Ended", data.get('ended_at', 'N/A')),
                ("Total Entries", str(len(data.get('entries', [])))),
            ]
            
            # Create table using raw LaTeX
            table_lines = [
                r'\begin{tabular}{|l|l|}',
                r'\hline',
                r'\textbf{Field} & \textbf{Value} \\',
                r'\hline',
            ]
            for key, value in metadata:
                safe_value = escape_latex(truncate_text(value, 60))
                table_lines.append(f'{escape_latex(key)} & {safe_value} \\\\')
                table_lines.append(r'\hline')
            table_lines.append(r'\end{tabular}')
            
            self.doc.append(NoEscape('\n'.join(table_lines)))
            self.doc.append(NoEscape('\n'))
    
    def _add_analytics_section(self, data: dict):
        """Add analytics section to document."""
        entries = data.get('entries', [])
        
        with self.doc.create(Section('Analytics')):
            # Entry type distribution
            type_counts = {}
            for entry in entries:
                entry_type = entry.get('type', 'unknown')
                type_counts[entry_type] = type_counts.get(entry_type, 0) + 1
            
            with self.doc.create(Subsection('Entry Type Distribution')):
                if type_counts:
                    # Table
                    table_lines = [
                        r'\begin{tabular}{|l|c|}',
                        r'\hline',
                        r'\textbf{Type} & \textbf{Count} \\',
                        r'\hline',
                    ]
                    for entry_type, count in sorted(type_counts.items()):
                        table_lines.append(f'{escape_latex(entry_type)} & {count} \\\\')
                        table_lines.append(r'\hline')
                    table_lines.append(r'\end{tabular}')
                    self.doc.append(NoEscape('\n'.join(table_lines)))
                    self.doc.append(NewLine())
                    
                    # Bar chart - use simple tabular instead of pgfplots to avoid issues
                    # Skip chart if too many types or has problematic names
                    if len(type_counts) <= 8 and not any('-' in t for t in type_counts.keys()):
                        sorted_types = sorted(type_counts.items())
                        chart_data = ', '.join([f'({escape_latex(t)}, {c})' for t, c in sorted_types])
                        bar_chart = NoEscape(r"""
\begin{tikzpicture}
\begin{axis}[
    ybar,
    bar width=20pt,
    width=\textwidth,
    height=8cm,
    ylabel={Count},
    symbolic x coords={""" + ', '.join([escape_latex(t) for t, _ in sorted_types]) + r"""},
    xtick=data,
    x tick label style={rotate=45, anchor=east},
    nodes near coords,
    nodes near coords align={vertical},
]
\addplot coordinates {""" + chart_data + r"""};
\end{axis}
\end{tikzpicture}
""")
                        self.doc.append(bar_chart)
            
            # Tool usage
            tool_counts = {}
            for entry in entries:
                if entry.get('type') == 'tool':
                    tool = entry.get('tool', 'unknown')
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
            
            if tool_counts:
                with self.doc.create(Subsection('Tool Usage')):
                    # Table
                    table_lines = [
                        r'\begin{tabular}{|l|c|}',
                        r'\hline',
                        r'\textbf{Tool} & \textbf{Count} \\',
                        r'\hline',
                    ]
                    for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
                        table_lines.append(f'{escape_latex(tool)} & {count} \\\\')
                        table_lines.append(r'\hline')
                    table_lines.append(r'\end{tabular}')
                    self.doc.append(NoEscape('\n'.join(table_lines)))
                    self.doc.append(NewLine())
                    
                    # Simple bar chart using tikz without pgfplots
                    sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10
                    max_count = max(c for _, c in sorted_tools) if sorted_tools else 1
                    
                    tikz_lines = [r'\begin{tikzpicture}', r'\begin{scope}[xscale=0.5]']
                    for i, (tool, count) in enumerate(sorted_tools):
                        bar_width = count / max_count * 10
                        tikz_lines.append(f'\\draw[fill=blue!70] (0,{i*0.6}) rectangle ({bar_width},{i*0.6+0.4}) node[midway,right] {{{escape_latex(tool)}: {count}}};')
                    tikz_lines.extend([r'\end{scope}', r'\end{tikzpicture}'])
                    self.doc.append(NoEscape('\n'.join(tikz_lines)))
            
            self.doc.append(NoEscape('\n'))
    
    def _add_conversation_section(self, data: dict, max_text_length: int = 300, max_entries: int = 100):
        """Add conversation section to document."""
        entries = data.get('entries', [])
        included = 0
        
        with self.doc.create(Section('Conversation')):
            for idx, entry in enumerate(entries):
                if included >= max_entries:
                    self.doc.append(NoEscape(r'\textit{\small [truncated — showing first 100 entries]}'))
                    break
                
                entry_type = entry.get('type', 'unknown')
                
                # Skip side-effect entries
                if entry_type == 'side-effect':
                    included += 1
                    continue
                
                # Handle ACTION entries - show actual commands with commentary
                if entry_type == 'action':
                    tool = entry.get('tool', 'unknown')
                    text = entry.get('text', '')
                    status = entry.get('status', '')
                    
                    if text and '{' in str(text):
                        # Parse JSON to extract command and description
                        try:
                            import json as json_mod
                            cmd_data = json_mod.loads(text)
                            command = cmd_data.get('command', '')
                            description = cmd_data.get('description', '')
                            workdir = cmd_data.get('workdir', '')
                            
                            # Show description as commentary
                            if description:
                                self.doc.append(NoEscape(f'\\textit{{\\small {escape_latex(description)}}}'))
                                self.doc.append(NoEscape('\n'))
                            
                            # Show the actual command in a code block
                            if command:
                                self.doc.append(NoEscape(r'\begin{lstlisting}[language=bash]'))
                                self.doc.append(command)
                                self.doc.append(NoEscape(r'\end{lstlisting}'))
                            
                            # Show workdir if different from default
                            if workdir and 'AgentSON' not in workdir:
                                self.doc.append(NoEscape(f'\\textit{{\\tiny in: {escape_latex(workdir)}}}'))
                                self.doc.append(NoEscape('\n'))
                            
                            # Show status
                            if status:
                                color = 'green' if status == 'completed' else 'red'
                                self.doc.append(NoEscape(f'\\textcolor{{{color}}}{{\\small [{escape_latex(status)}]}}'))
                        except:
                            # Fallback - just show as code
                            self.doc.append(NoEscape(r'\begin{lstlisting}[language=bash]'))
                            self.doc.append(truncate_text(text, 300))
                            self.doc.append(NoEscape(r'\end{lstlisting}'))
                    else:
                        # Non-JSON action - show tool name
                        self.doc.append(NoEscape(f'\\textcolor{{gray}}{{ACTION: {escape_latex(tool)}}}'))
                    
                    self.doc.append(NoEscape('\n'))
                    self.doc.append(NoEscape('\n'))
                    included += 1
                    continue
                
                # Handle USER-QUERY entries
                if entry_type == 'user-query':
                    text = entry.get('text', entry.get('query', ''))
                    if text:
                        self.doc.append(NoEscape(r'\textbf{User:}'))
                        self.doc.append(NoEscape('\n'))
                        self.doc.append(NoEscape(r'\parbox{\textwidth}{'))
                        self.doc.append(escape_latex(str(text)))
                        self.doc.append(NoEscape('}'))
                    self.doc.append(NoEscape('\n'))
                    self.doc.append(NoEscape('\n'))
                    included += 1
                    continue
                
                # Handle ANSWER entries (assistant responses)
                if entry_type == 'answer':
                    text = entry.get('text', '')
                    if text:
                        self.doc.append(NoEscape(r'\textbf{Assistant:}'))
                        self.doc.append(NoEscape('\n'))
                        # For answers, show more text but still truncate
                        text = truncate_text(str(text), 400)
                        self.doc.append(NoEscape(r'\parbox{\textwidth}{'))
                        self.doc.append(escape_latex(text))
                        self.doc.append(NoEscape('}'))
                    self.doc.append(NoEscape('\n'))
                    self.doc.append(NoEscape('\n'))
                    included += 1
                    continue
                
                # Handle THOUGHT entries
                if entry_type == 'thought':
                    text = entry.get('text', '')
                    if text:
                        self.doc.append(NoEscape(r'\textit{\small [thinking]}'))
                        self.doc.append(NoEscape('\n'))
                        text = truncate_text(str(text), 150)
                        self.doc.append(NoEscape(r'\parbox{0.9\textwidth}{'))
                        self.doc.append(escape_latex(text))
                        self.doc.append(NoEscape('}'))
                    self.doc.append(NoEscape('\n'))
                    self.doc.append(NoEscape('\n'))
                    included += 1
                    continue


def export_to_pdf(input_path: str, output_path: str = None, **kwargs) -> str:
    """Export an .agentson file to PDF."""
    exporter = AgentSONPDFExporter()
    return exporter.export(input_path, output_path, **kwargs)


def export_all_to_pdf(input_dir: str = "examples", output_dir: str = "exports/pdf"):
    """Export all .agentson files in a directory to PDF."""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    agentson_files = list(input_path.glob("*.agentson"))
    
    if not agentson_files:
        print(f"No .agentson files found in {input_dir}")
        return
    
    print(f"Found {len(agentson_files)} .agentson files")
    
    exported = 0
    failed = 0
    
    for agentson_file in agentson_files:
        try:
            output_file = output_path / f"{agentson_file.stem}.pdf"
            export_to_pdf(str(agentson_file), str(output_file))
            exported += 1
        except Exception as e:
            print(f"Error exporting {agentson_file.name}: {e}")
            failed += 1
    
    print(f"\nExported {exported} files, failed {failed}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export AgentSON to PDF")
    parser.add_argument("input", help="Input .agentson file or directory")
    parser.add_argument("--output", help="Output .pdf file or directory")
    parser.add_argument("--all", action="store_true", help="Export all .agentson files in directory")
    parser.add_argument("--max-text", type=int, default=300, help="Max text length per entry")
    parser.add_argument("--no-analytics", action="store_true", help="Skip analytics section")
    args = parser.parse_args()
    
    if args.all:
        export_all_to_pdf(args.input, args.output or "exports/pdf")
    else:
        export_to_pdf(args.input, args.output, 
                      max_text_length=args.max_text,
                      include_analytics=not args.no_analytics)
