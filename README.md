# Cricket stats

See the blog post: [Analysing cricket statistics in Pandas][blog].

To run locally:

```shell
asdf install
pip install -r requirements.txt
```

Then run the Python scripts. For instance, to scrape the latest data
from Statsguru, `python update_data.py`. To cache the HTML from
Statsguru (to make future scrapes faster), set `STATSGURU_CACHE=cache`
(or another directory of your choosing.

[blog]: https://brasier.me/pandas/2020/06/10/neeerd-pledge/
