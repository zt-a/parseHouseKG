import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parsehousekg.crawl import crawl_category


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Parse house.kg kupit")
    p.add_argument("--category", default="buy_all", help="buy_all|buy_house|buy_apart|buy_land|buy_room|buy_commercial|buy_dacha|buy_parking")
    p.add_argument("--limit", type=int, default=10000, help="max details to collect")
    p.add_argument("--max-pages", type=int, default=None, help="max list pages to traverse")
    p.add_argument("--db", default="housekg.db", help="sqlite db path")
    args = p.parse_args()

    res = crawl_category(
        category_key=args.category,
        limit=args.limit,
        max_pages=args.max_pages,
        db_path=args.db,
        skip_existing=True,
        update_existing=False,
    )
    print(res)


if __name__ == "__main__":
    main()
