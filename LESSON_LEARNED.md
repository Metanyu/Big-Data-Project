## Loại Lỗi,Triệu chứng (Log),Nguyên nhân gốc rễ,Giải pháp

- Networking,Connection refused (Spark -> DataNode),"DataNode gửi IP nội bộ (Container IP) cho Spark, nhưng Spark ở container khác không truy cập được IP đó.", Fix Config: Thêm HDFS_CONF_dfs_datanode_use_datanode_hostname=true vào compose.yaml để ép dùng hostname.

- Port Mapping,Connection refused (Spark -> NameNode),"Spark cố kết nối cổng chuẩn 9000, nhưng Image Hadoop bde2020 mặc định chạy cổng 8020.",Đồng bộ: Sửa config Spark HDFS_NAMENODE và fs.defaultFS về cổng 8020.

- Metadata,DataNode tự shutdown sau khi restart,"Lỗi ""Râu ông nọ cắm cằm bà kia"". NameNode format lại tạo ClusterID mới, nhưng DataNode vẫn giữ ClusterID cũ trong volume.",Hard Reset: Dùng docker compose down -v để xóa sạch volume và tạo lại từ đầu.

- Permission,"Permission denied: user=spark, access=WRITE","Spark chạy với user spark, nhưng thư mục gốc / của HDFS thuộc về root.",Cấp quyền: Chạy hdfs dfs -mkdir và hdfs dfs -chmod -R 777 /taxi_data từ container NameNode.
- Race Condition,AnalysisException: Couldn't find table,Spark khởi động và chạy code trước khi Cassandra kịp tạo bảng xong.,Quy trình: Luôn đợi Cassandra khỏe (Healthy) và chạy lệnh init.cql trước khi bật Spark.

## Hướng dẫn scale
- Nếu bạn chuyển sang máy 16GB RAM, hãy "mở khóa" sức mạnh của hệ thống bằng các điều chỉnh sau:

1. Trong compose.yaml 
- Spark: Tăng RAM cho Driver và Executor.YAMLcommand: 
>
  ...
  --driver-memory 4G  # Tăng từ 1.5G -> 4G
  --executor-memory 4G # Tăng từ 1.5G -> 4G
  --executor-cores 2   # Cho phép xử lý song song thực sự

- Cassandra: Tăng Heap Size để chịu tải ghi cao hơn.
YAML environment:
  - MAX_HEAP_SIZE=4G
  - HEAP_NEWSIZE=800M

2. Trong spark/streaming.py (Bật full tính năng):
- Bật lại các Stream đã tắt: Uncomment các dòng get_zone_agg (1h), get_peak_agg, get_payment_agg để tính toán đầy đủ các chỉ số.
- Tăng tốc độ HDFS: Giảm thời gian trigger để dữ liệu vào Data Lake nhanh hơn, từ 1 phút xuống còn 30s hoặc bỏ trigger để chạy real-time (default)
- Tăng parallelism: Sửa master("local[2]") thành master("local[*]") để tận dụng hết số nhân CPU của máy.