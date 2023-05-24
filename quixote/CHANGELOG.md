# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

# [0.0.4] - 2024-05-23

### Added
    - Button to list.html template to export csv data 
    -
    

### Fixed
    - Wrong display of fields in list.html

### Changed
    -

### Removed
    - Commented import to FileSystemStorage in views.py for sancho app

## [0.0.3] - 2024-05-23

### Added
    - Additional fields to processed.html templated after processing backtest.
    - processed.html template now showing number of processed backtest.
    - ProcessBacktests view added lists to handle and pass BtGenbox and BtMetrics objects. 
    

### Fixed
    - context variable to pass to processed.html passing a list of dicts 

### Changed
    - Properly comments on variables in `post` method in ProcessBacktest view.
    - ProcessBacktest view now passes BtGenbox and BtMetrics list of objects in context.
    - valid manager from Metrics model to Backtest model
    - valid manager included Backtest.PeriodType.ISOS condition to retrieve only backtests
      where the ISOS is valid.
    - Report time to process backtests in seconds (Debug Mode Only)

### Removed
    - `Archivos procesados` unordered list from processed.html
    


## [0.0.2] - 2023-05-23

### Added
    - All metrics added to view to process uploaded backtests

### Fixed
    - Bulk insert into database
    - Blank space in base.html for sancho for /static/css folder
    - Processed.html view not showing results after processing backtests

### Changed
    - Processed.html template to accept the context from ProcessBacktest
    - DATA_UPLOAD_MAX_NUMBER_FILES value changed to 1000 in project settings.py
    - Process.html shows D1 as default selected timeframe - before it was M1.

### Removed
    - Backtests directory in sancho/src
    - bt.py file inside sancho/src/parser


## [0.0.1] - 2023-05-22

### Added
    - Basic view to process uploaded backtests

### Fixed

### Changed

### Removed

