# 持仓信息表格的css

headers = {
    'selector': 'th.col_heading',
    'props': [
        ('background-color', 'black'),
        ('color', 'white'),
        ('border-bottom', '1px solid green'),
        ('border-top', '1px solid green'),
        ('text-align', 'center'),
        ('border-left', 'none'),
        ('border-right', 'none')
    ]
}

left_header_border = {
    'selector': 'th.col_heading:first-child',
    'props': [('border-left', '1px solid green')]
}

right_header_border = {
    'selector': 'th.col_heading:last-child',
    'props': [('border-right', '1px solid green')]
}

alternate_rows = {
    'selector': 'tbody tr:nth-child(even)',
    'props': [
        ('background-color', 'rgba(0, 30, 10)')
    ]
}

rows = [
    {
        'selector': 'tbody tr',
        'props': [
            ('background-color', 'black'),
            ('color', 'white'),
            ('border', '1px solid green'),
            ('text-align', 'center')
        ]
    },
    alternate_rows,
    {
        'selector': 'td',
        'props': [
            ('border-left', 'none'),
            ('border-right', 'none')
        ]
    }
]
