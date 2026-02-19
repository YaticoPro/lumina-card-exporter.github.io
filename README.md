# Project Title

Card exporter project

## Description

A mini project that exports Lumina cards from CSV file (or
exportable as CSV GoogleSheets document)

## Getting Started

Runs with [Python > 3.12](https://www.python.org/)

### Dependencies

[Poetry](https://python-poetry.org/)

### Installing

```
poetry install
```

### Executing program

For IntelliJ / PyCharm users, use the `.idea/runConfigurations/main.xml` 
configuration file, and change the link to your exportable GoogleSheets file

Otherwise,

* If you are getting the data from Google Sheets
```
poetry python main.py
--link
"https://docs.google.com/spreadsheets/d/your-id-to-google-sheets-doc/export?format=csv"
--dp
True
--di
True
```
* If you are getting the data from a local CSV file
```
poetry python main.py
--cp
"path/to/your/csv/file"
--dp
True
--di
True
```

## FAQ

- **_Why not all my cards exported ?_** The id used to distinguish the cards is the id.
If the id of two cards are the same, the first to be processed will be erased
over the second one
- **_Can I change some elements without changing the code ?_** Yes, you can change the police, card elements, 
and the colors as long as the paths of the elements do not change. All no-code configuration is in `/card_elements/`
**_/!\ To keep the good size of the card, the background image `card_elements/image_elements/image_background.png` 
must be a 744x1039 pixels image, otherwise, the size and alignment of all the elements in the image card will be wrong_**

## Authors
[Yann Tireau](https://github.com/YaticoPro)