import json
from io import StringIO
import pandas as pd
import matplotlib.pyplot as plt

def output_formatter(content):
    try:
        content = json.loads(content)

        if content['content_type'] == "markdown":
            return content['content']

        if content['content_type'] == "dataframe":
            df = pd.read_csv(StringIO(content['content']), delimiter="|", skiprows=[1], skipinitialspace=True, engine='python')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')].apply(lambda x: x.str.strip())

            return df

        if content['content_type'] == "matplotlib":
            return plt.figure(content['content'])

        if content['content_type'] == "image":
            return content['content']

        return content['content']

    except:
        # if the content isn't json, return it as is
        pass

    return content

__all__ = ["output_formatter",]
