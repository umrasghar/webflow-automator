# WebFlow Automator

![WebFlow Automator Logo](docs/images/logo.png)

WebFlow Automator is a standalone desktop application for visually automating web-based workflows. It allows you to create, record, and execute browser automation sequences without writing code.

## Features

- **Visual Element Selection**: Point and click to interact with web elements
- **Workflow Builder**: Create automation sequences with a drag-and-drop interface
- **Dynamic Data Generation**: Generate realistic test data for forms
- **Variable Management**: Store and reuse data across workflow steps
- **Excel Integration**: Import and export data to Excel files
- **No Coding Required**: Build complex automations without writing a single line of code
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Use Cases

- **QA Testing**: Automate repetitive testing tasks
- **Data Entry**: Fill forms with generated or imported data
- **Web Scraping**: Extract and save data from websites
- **Process Automation**: Automate business processes and workflows
- **Batch Processing**: Process multiple data records in sequence

## Screenshots

![Main UI](docs/images/main-ui.png)

*WebFlow Automator main interface*

![Workflow Builder](docs/images/workflow-builder.png)

*Creating automation workflows*

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/webflow-automator.git

# Navigate to the project directory
cd webflow-automator

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

For detailed installation instructions, see the [Installation Guide](docs/installation.md).

### Creating Your First Workflow

1. Launch WebFlow Automator
2. Click "New Workflow"
3. Add a "Navigate to URL" action
4. Add interaction actions (click, type, etc.)
5. Save your workflow
6. Click "Start" to run it

For a more comprehensive guide, see the [Getting Started Guide](docs/getting-started.md).

## Architecture

WebFlow Automator is built with a modular architecture that separates concerns:

- **UI Module**: Handles the user interface and user interactions
- **Automation Engine**: Manages browser control and element interactions
- **Data Manager**: Handles variables, data generation, and Excel integration
- **Workflow Manager**: Manages workflow creation, storage, and execution

## Dependencies

- Python 3.8+
- PyQt6/PySide6 for UI
- Selenium for browser automation
- pandas and openpyxl for Excel integration
- Faker for data generation

## Roadmap

- [x] Basic workflow builder
- [x] Element interaction (click, type, select)
- [x] Variable management
- [x] Data generation
- [x] Excel integration
- [ ] Conditional logic
- [ ] Loops and iterations
- [ ] PDF form automation
- [ ] Scheduler for automated runs
- [ ] Cloud sync for workflows

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Selenium](https://www.selenium.dev/) - Browser automation framework
- [PyQt/PySide](https://www.qt.io/) - UI framework
- [pandas](https://pandas.pydata.org/) - Data manipulation library
- [Faker](https://faker.readthedocs.io/) - Test data generation library

---

*WebFlow Automator is not affiliated with any web automation service or company. It is an open-source tool created for educational and productivity purposes.*