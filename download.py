import requests
import os
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
from tqdm import tqdm
import psutil
import sys

class WallhavenBatchDownloader:
    def __init__(self, txt_file="wallhaven_links.txt", save_dir="batch_download", max_workers=4):
        self.txt_file = txt_file
        self.save_dir = save_dir
        self.max_workers = max_workers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.success_count = 0
        self.fail_count = 0
        self.lock = threading.Lock()
    
    def load_links(self):
        """读取TXT文件链接 - 自动解析各种格式"""
        if not os.path.exists(self.txt_file):
            print(f"❌ 文件不存在: {self.txt_file}")
            return []
        
        # 支持4种格式自动解析
        patterns = [
            r'https://wallhaven\.cc/w/[a-z0-9]{6}',  # 纯链接
            r'\[https://wallhaven\.cc/w/[a-z0-9]{6}\]',  # [链接]
            r'\(https://wallhaven\.cc/w/[a-z0-9]{6}\)',  # (链接)
            r'https://wallhaven\.cc/w/[a-z0-9]{6}[)\]]?',  # 链接]
        ]
        
        links = []
        duplicates = set()
        
        with open(self.txt_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # 尝试所有正则模式
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        # 清理链接
                        clean_link = re.sub(r'[\[\]()]', '', match)
                        if (clean_link.startswith('https://wallhaven.cc/w/') and 
                            len(clean_link.split('/')[-1]) == 6 and 
                            clean_link not in duplicates):
                            links.append(clean_link)
                            duplicates.add(clean_link)
                            break  # 找到有效链接就跳出
                
                # 显示解析过程（前5行）
                if line_num <= 5:
                    found = [m for pattern in patterns for m in re.findall(pattern, line)]
                    if found:
                        print(f"📖 第{line_num}行解析: {line[:60]}... -> {found[0][:50]}...")
        
        print(f"✅ 从 {self.txt_file} 自动解析出 {len(links)} 个有效链接")
        if len(links) == 0:
            print("💡 提示: 文件格式示例:")
            print("  1. https://wallhaven.cc/w/l853yp")
            print("  2. [https://wallhaven.cc/w/ogy6zm](https://wallhaven.cc/w/ogy6zm)")
            print("  3. (https://wallhaven.cc/w/zpzd3j)")
        return links
    
    def get_image_info(self, wall_link):
        """获取单个壁纸原图信息"""
        wallpaper_id = wall_link.split('/')[-1]
        try:
            api_url = f"https://wallhaven.cc/api/v1/w/{wallpaper_id}"
            resp = requests.get(api_url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()['data']
                return wallpaper_id, data['path']
        except:
            pass
        return wallpaper_id, None
    
    def download_image(self, wall_link):
        """下载单个壁纸"""
        wallpaper_id, img_url = self.get_image_info(wall_link)
        if not img_url:
            with self.lock:
                self.fail_count += 1
            return False
        
        try:
            img_resp = requests.get(img_url, headers=self.headers, 
                                  stream=True, timeout=30)
            if img_resp.status_code == 200:
                ext = img_url.split('.')[-1].split('?')[0]
                filename = f"{wallpaper_id}.{ext}"
                filepath = os.path.join(self.save_dir, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in img_resp.iter_content(8192):
                        f.write(chunk)
                
                size_mb = img_resp.headers.get('content-length', 0)
                size_mb = float(size_mb) / 1024 / 1024 if size_mb else 0
                
                with self.lock:
                    self.success_count += 1
                    self.print_progress(wallpaper_id, size_mb, filename)
                
                img_resp.close()
                del img_resp
                gc.collect()
                return True
        except:
            pass
        
        with self.lock:
            self.fail_count += 1
        return False
    
    def print_progress(self, wallpaper_id, size_mb, filename):
        """美化进度输出"""
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        
        sys.stdout.write(f"\r🎨 [{self.success_count:3d}/{self.total:3d}] "
                        f"{wallpaper_id} ({size_mb:5.1f}MB) "
                        f"💾{self.fail_count} | "
                        f"🧠{mem_mb:4.0f}MB")
        sys.stdout.flush()
    
    def monitor_memory(self):
        """内存监控线程"""
        while getattr(self, 'running', False):
            process = psutil.Process()
            mem_mb = process.memory_info().rss / 1024 / 1024
            if mem_mb > 3000:
                gc.collect()
                print(f"\n🧹 内存清理: {mem_mb:.0f}MB -> ", end="")
            time.sleep(5)
    
    def download(self):
        """多线程批量下载主函数"""
        print("🚀 Wallhaven 多线程批量下载器 (智能解析版)")
        print("=" * 60)
        
        links = self.load_links()
        if not links:
            return
        
        self.total = len(links)
        self.running = True
        os.makedirs(self.save_dir, exist_ok=True)
        
        mem_thread = threading.Thread(target=self.monitor_memory, daemon=True)
        mem_thread.start()
        
        print(f"\n⚙️  配置: {self.max_workers}线程 | "
              f"目标: {self.total}张 | "
              f"保存: {os.path.abspath(self.save_dir)}")
        print("📥 开始下载...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.download_image, link) for link in links]
            
            with tqdm(total=self.total, desc="进度", 
                     bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
                for future in as_completed(futures):
                    pbar.update(1)
        
        self.running = False
        
        print("\n" + "=" * 60)
        print(f"🎉 下载完成!")
        print(f"✅ 成功: {self.success_count}/{self.total}")
        print(f"❌ 失败: {self.fail_count}")
        print(f"📁 保存: {os.path.abspath(self.save_dir)}")
        gc.collect()

# 一键使用
if __name__ == "__main__":
    downloader = WallhavenBatchDownloader(
        txt_file="wallhaven_hot_P20.txt",  # 你的原始文件
        save_dir="ultra_hd_wallpapers",
        max_workers=4
    )
    downloader.download()
