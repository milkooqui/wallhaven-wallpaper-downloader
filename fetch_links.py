import requests
import time

def get_wallhaven_links(sorting="hot", pages=10, per_page=24):
    all_links = []

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Connection": "keep-alive"
    })

    for page in range(1, pages + 1):
        url = (
            f"https://wallhaven.cc/api/v1/search"
            f"?sorting={sorting}&per_page={per_page}&page={page}"
        )

        print(f"获取第 {page}/{pages} 页...")

        success = False
        for attempt in range(3):
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    page_links = [
                        f"https://wallhaven.cc/w/{item['id']}"
                        for item in data.get("data", [])
                    ]
                    all_links.extend(page_links)
                    print(f"✓ 第 {page} 页成功：{len(page_links)} 张")
                    success = True
                    break
                else:
                    print(f"⚠ 状态码异常: {resp.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⚠ 请求失败（第 {attempt+1} 次）: {e}")
                time.sleep(2 + attempt * 2)

        if not success:
            print(f"❌ 第 {page} 页跳过")

        time.sleep(2)

    return all_links


def save_links_to_txt(links, filename):
    """保存壁纸链接到 TXT 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Wallhaven 壁纸链接\n")
        f.write(f"# 总数: {len(links)}\n\n")
        for link in links:
            f.write(link + "\n")

    print(f"💾 已保存 {len(links)} 个链接到 {filename}")
    return filename


if __name__ == "__main__":
    # 自测入口（可选）
    links = get_wallhaven_links(pages=2)
    save_links_to_txt(links, "test_links.txt")
