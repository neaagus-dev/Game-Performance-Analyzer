# Game Performance Analyzer

Game Performance Analyzer is a Streamlit web application used to analyze performance logs generated with MSI Afterburner.
The application reads hardware monitoring data from `.hml`, `.csv`, or `.txt` log files and displays the results through visual dashboards, performance graphs, spike detection, and an automatically generated PDF report.

## Project Purpose

The purpose of this project is to make performance data easier to understand and interpret.
MSI Afterburner can record many hardware metrics during the execution of a game or graphical application, but the raw log file is difficult to read manually.

This application processes the log file and transforms the raw data into useful information such as:

* average FPS;
* average frame time;
* CPU usage;
* GPU usage;
* GPU temperature;
* CPU temperature;
* FPS drops and performance spikes;
* graphical performance evolution;
* downloadable PDF report.

## Technologies Used

The project was developed using:

* Python
* Streamlit
* Pandas
* Matplotlib
* ReportLab
* MSI Afterburner

## Features

The application includes the following features:

* upload MSI Afterburner log files;
* automatic parsing of hardware monitoring data;
* support for FPS, frame time, CPU usage, GPU usage, GPU temperature and CPU temperature;
* performance summary using metric cards;
* FPS spike detection based on a configurable threshold;
* table with the most severe FPS drops;
* performance graphs for all available metrics;
* PDF report generation;
* English interface.

## Application Workflow

The application follows this workflow:

```text
Game / Graphical Application
        ↓
MSI Afterburner
        ↓
Hardware Monitoring Log
        ↓
Python Data Processing
        ↓
Streamlit Dashboard
        ↓
PDF Performance Report
```

## MSI Afterburner Configuration

To generate a compatible log file, MSI Afterburner should be configured to monitor the following metrics:

* GPU temperature
* GPU usage
* CPU temperature
* CPU usage
* Framerate
* Frametime

The option **Log history to file** must be enabled from the Monitoring tab.

After running a game or graphical application, MSI Afterburner will generate a hardware monitoring log file.
This file can then be uploaded into the Streamlit application.

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/game-performance-analyzer.git
```

Enter the project folder:

```bash
cd game-performance-analyzer
```

Install the required dependencies:

```bash
pip install streamlit pandas matplotlib reportlab
```

## Running the Application

Run the application using:

```bash
streamlit run app.py
```

After running the command, the application will open in the browser.

## PDF Report

The application can generate a PDF report containing:

* performance summary;
* average, minimum and maximum values;
* FPS threshold used for spike detection;
* number of detected FPS spikes;
* table with the most severe FPS drops;
* performance graphs.

This report is useful for presenting and comparing performance results in a structured format.

## Future Improvements

Possible future improvements include:

* comparing multiple performance sessions;
* real-time monitoring;
* exporting reports in multiple formats;
* adding more advanced anomaly detection;
* improving the dashboard design;
* supporting more log formats.

## Author

Agus Nicoleta Estera
Faculty of Automation, Computers and Electronics
Specialization: Automation and Applied Informatics
