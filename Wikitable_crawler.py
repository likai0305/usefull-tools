import urllib.request
from bs4 import BeautifulSoup

web_page = 'https://en.wikipedia.org/wiki/List_of_Olympic_Games_host_cities'
page = urllib.request.urlopen(web_page)
soup = BeautifulSoup(page, 'html.parser')
table = soup.find("table", {"class": "wikitable sortable"})

def clean_data(row):
    cleaned_cells = []
    for cell in row:
        references = cell.findAll('sup', {'class': 'reference'})
        if references:
            for ref in references:
                ref.extract()
        sortkeys = cell.findAll("span", {"class": "sortkey"})
        if sortkeys:
            for ref in sortkeys:
                ref.extract()
        text_items = cell.findAll(text=True)
        no_footnotes = [text for text in text_items if text[0] != '[']
        cleaned = (
            ''.join(no_footnotes)
            .replace('\xa0', ' ')
            .replace('\n', ' ')
            .strip()
        )
        cleaned_cells += [cleaned]
    return cleaned_cells


def html_to_table(table):
    result = []
    saved_rowspans = []
    saved_colspans = []
    for row in table.findAll('tr'):
        cells = row.findAll(['th', 'td'])
        if len(saved_rowspans) == 0:
            saved_rowspans = [None for _ in cells]
            saved_colspans = [None for _ in cells]
        elif len(cells) != len(saved_rowspans):
            for index, rowspan_data in enumerate(saved_rowspans):
                if rowspan_data is not None and saved_colspans[index] is None:
                    # Insert the data from previous row; decrement rows left
                    value = rowspan_data['value']
                    cells.insert(index, value)
                    # Check the rows span number
                    if saved_rowspans[index]['rows_left'] == 2:
                        saved_rowspans[index] = None
                    else:
                        saved_rowspans[index]['rows_left'] -= 1
                if rowspan_data is not None and saved_colspans[index] is not None:
                    # Copy the index to deal with the column data
                    idx = index
                    # Insert the data from previous row; decrement rows left
                    value = rowspan_data['value']
                    cells.insert(index, value)
                    # Check the rows span number
                    if saved_rowspans[index]['rows_left'] == 2:
                        saved_rowspans[index] = None
                    else:
                        saved_rowspans[index]['rows_left'] -= 1
                    # Copy the column data from previous column span data
                    colspan_data_copy = saved_colspans[index].copy()
                    while colspan_data_copy['cols_left'] >= 2:
                        value = colspan_data_copy['value']
                        idx = idx + 1
                        cells.insert(idx, value)
                        colspan_data_copy['cols_left'] = colspan_data_copy['cols_left'] - 1
                        # If the row span had been finished, then reset the column span data to None
                        if saved_rowspans[index] == None:
                            saved_colspans = [None for _ in range(8)]
        for idx, cell in enumerate(cells):
            if cell.has_attr('rowspan') and cell.has_attr('colspan'):
                rows_left = int(cell["rowspan"])
                cols_left = int(cell["colspan"])
                cell.attrs = []
                rowspan_data = {
                    'rows_left': rows_left,
                    'value': cell
                }
                colspan_data = {
                    'cols_left': cols_left,
                    'value': cell
                }
                saved_rowspans[idx] = rowspan_data
                saved_colspans[idx] = colspan_data
                colspan_data_copy = colspan_data.copy()
                while colspan_data_copy['cols_left'] >= 2:
                    value = colspan_data_copy['value']
                    idx = idx + 1
                    cells.insert(idx, value)
                    colspan_data_copy['cols_left'] = colspan_data_copy['cols_left'] - 1
            if cell.has_attr('rowspan') and not cell.has_attr('colspan'):
                rows_left = int(cell["rowspan"])
                cell.attrs = []
                rowspan_data = {
                    'rows_left': rows_left,
                    'value': cell
                }
                saved_rowspans[idx] = rowspan_data
            if cell.has_attr('colspan') and not cell.has_attr('rowspan'):
                cols_left = int(cell["colspan"])
                cell.attrs = []
                colspan_data = {
                    'cols_left': cols_left,
                    'value': cell
                }
                while colspan_data['cols_left'] >= 2:
                    value = colspan_data['value']
                    idx = idx + 1
                    cells.insert(idx, value)
                    colspan_data['cols_left'] = colspan_data['cols_left'] - 1
        if cells:
            cleaned = clean_data(cells)
            columns_missing = len(saved_rowspans) - len(cleaned)
            if columns_missing:
                cleaned += [None] * columns_missing
            result.append(cleaned)
    return result