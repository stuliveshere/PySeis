import fitz  # PyMuPDF
import sys

class PDFViewer:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pages = []
        self.load_pdf()
        
    def load_pdf(self):
        """Load all pages from PDF into memory."""
        pdf_document = fitz.open(self.pdf_path)
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text = page.get_text()
            self.pages.append(text)
        self.total_pages = len(self.pages)
    
    def print_page(self, page_num):
        """Print a specific page (1-based indexing)."""
        if 1 <= page_num <= self.total_pages:
            print(f"\nPage {page_num}:")
            print("-" * 80)
            print(self.pages[page_num - 1])
            print("-" * 80)
        else:
            print(f"Error: Page number must be between 1 and {self.total_pages}")
    
    def dump_to_file(self, output_file):
        """Dump all pages to a text file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            for page_num, text in enumerate(self.pages, start=1):
                f.write(f"Page {page_num}:\n")
                f.write("-" * 80 + "\n")
                f.write(text + "\n")
                f.write("-" * 80 + "\n")
        print(f"Dumped all pages to {output_file}")
    
    def show_help(self):
        """Show help message."""
        print("\nCommands:")
        print("  p <num>  - Print page number <num>")
        print("  r <start> <end> - Print range of pages")
        print("  t        - Show total pages")
        print("  d <file> - Dump all pages to <file>")
        print("  h        - Show this help")
        print("  q        - Quit")
    
    def run(self):
        """Run the interactive viewer."""
        print(f"Loaded PDF with {self.total_pages} pages")
        self.show_help()
        
        while True:
            try:
                command = input("\nEnter command: ").strip().split()
                if not command:
                    continue
                
                if command[0] == 'q':
                    break
                    
                elif command[0] == 'h':
                    self.show_help()
                    
                elif command[0] == 't':
                    print(f"Total pages: {self.total_pages}")
                    
                elif command[0] == 'd' and len(command) == 2:
                    output_file = command[1]
                    self.dump_to_file(output_file)
                    
                elif command[0] == 'p' and len(command) == 2:
                    try:
                        page_num = int(command[1])
                        self.print_page(page_num)
                    except ValueError:
                        print("Error: Page number must be an integer")
                        
                elif command[0] == 'r' and len(command) == 3:
                    try:
                        start = int(command[1])
                        end = int(command[2])
                        if start <= end:
                            for page_num in range(start, end + 1):
                                self.print_page(page_num)
                        else:
                            print("Error: Start page must be less than or equal to end page")
                    except ValueError:
                        print("Error: Page numbers must be integers")
                        
                else:
                    print("Invalid command")
                    self.show_help()
                    
            except KeyboardInterrupt:
                print("\nUse 'q' to quit")
                continue
            except EOFError:
                break

if __name__ == "__main__":
    pdf_path = '../../data/seg_d_rev2.1.pdf'
    viewer = PDFViewer(pdf_path)
    viewer.run()
