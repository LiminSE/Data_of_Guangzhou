import os
import requests
import time

def fetch_osm_by_bbox(bbox, output_file):
    """
    按指定边界框（bbox）抓取 OSM 数据并保存为 .osm 文件。
    
    :param bbox: 边界框 (min_lat, min_lon, max_lat, max_lon)
    :param output_file: 输出的 .osm 文件名
    """
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:xml][timeout:3600];
    (
      node({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      way({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      relation({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );
    out meta;
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        print(f"正在抓取区域 {bbox} 数据...")
        response = requests.post(url, data=query, headers=headers)
        response.raise_for_status()
        osm_data = response.text

        # 保存数据到文件
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(osm_data)
        print(f"区域 {bbox} 的数据已保存为 {output_file}")
        time.sleep(2)  # 防止触发 API 限制

    except requests.exceptions.RequestException as e:
        print(f"请求失败：{e}")

def divide_area_to_bboxes(min_lat, max_lat, min_lon, max_lon, step):
    """
    将一个大范围区域划分为小网格区域，返回所有 bbox 列表。
    
    :param min_lat: 最小纬度
    :param max_lat: 最大纬度
    :param min_lon: 最小经度
    :param max_lon: 最大经度
    :param step: 每个网格的边长（经纬度差）
    :return: bbox 列表 [(min_lat, min_lon, max_lat, max_lon), ...]
    """
    bboxes = []
    lat_steps = int((max_lat - min_lat) / step) + 1
    lon_steps = int((max_lon - min_lon) / step) + 1
    for i in range(lat_steps):
        for j in range(lon_steps):
            bbox = (
                min_lat + i * step,
                min_lon + j * step,
                min(min_lat + (i + 1) * step, max_lat),
                min(min_lon + (j + 1) * step, max_lon),
            )
            bboxes.append(bbox)
    return bboxes

def merge_osm_files(input_folder, output_file):
    """
    合并多个 .osm 文件为一个完整的文件。
    
    :param input_folder: 存放 .osm 文件的目录
    :param output_file: 合并后的输出文件名
    """
    files = [f for f in os.listdir(input_folder) if f.endswith(".osm")]
    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        outfile.write('<osm version="0.6">\n')
        
        for file in files:
            with open(os.path.join(input_folder, file), "r", encoding="utf-8") as infile:
                for line in infile:
                    # 跳过 XML 声明和 <osm> 标签
                    if line.startswith('<?xml') or line.startswith('<osm') or line.startswith('</osm'):
                        continue
                    outfile.write(line)
        
        outfile.write('</osm>')
    print(f"合并完成，结果保存为 {output_file}")

def main():
    # Step 1: 定义广州市的经纬度范围
    min_lat, max_lat = 22.5, 23.5  # 纬度范围
    min_lon, max_lon = 112.5, 114.0  # 经度范围
    step = 0.1  # 每个小区域的边长

    # Step 2: 划分区域
    bboxes = divide_area_to_bboxes(min_lat, max_lat, min_lon, max_lon, step)

    # 创建输出目录
    output_folder = "osm_data"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Step 3: 分区域抓取数据
    for i, bbox in enumerate(bboxes):
        output_file = os.path.join(output_folder, f"guangzhou_part_{i + 1}.osm")
        fetch_osm_by_bbox(bbox, output_file)

    # Step 4: 合并所有抓取到的数据
    final_output_file = "guangzhou_full.osm"
    merge_osm_files(output_folder, final_output_file)

if __name__ == "__main__":
    main()