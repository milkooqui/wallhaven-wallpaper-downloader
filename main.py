import argparse
from fetch_links import get_wallhaven_links, save_links_to_txt
from download import WallhavenBatchDownloader


def main():
    parser = argparse.ArgumentParser(
        description="🎨 Wallhaven 壁纸批量下载器（CLI）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--sorting",
        choices=["hot", "toplist", "latest"],
        default="hot",
        help="壁纸排序方式"
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=10,
        help="提取页数（每页约 24 张）"
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="下载线程数（建议 2~4）"
    )

    parser.add_argument(
        "--output",
        default="wallpapers",
        help="壁纸保存目录"
    )

    parser.add_argument(
        "--links-only",
        action="store_true",
        help="只提取链接，不下载壁纸"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🎨 Wallhaven 壁纸工具启动")
    print(f"模式: {args.sorting}")
    print(f"页数: {args.pages}")
    print(f"线程: {args.threads}")
    print(f"仅提取链接: {'是' if args.links_only else '否'}")
    print("=" * 60)

    # 1️⃣ 提取链接
    links = get_wallhaven_links(
        sorting=args.sorting,
        pages=args.pages
    )

    if not links:
        print("❌ 未获取到任何链接，程序结束")
        return

    txt_file = save_links_to_txt(
        links,
        f"wallhaven_{args.sorting}_P{args.pages}.txt"
    )

    # 2️⃣ 是否下载
    if args.links_only:
        print("📄 已生成链接文件，未执行下载")
        return

    downloader = WallhavenBatchDownloader(
        txt_file=txt_file,
        save_dir=args.output,
        max_workers=args.threads
    )
    downloader.download()


if __name__ == "__main__":
    main()
