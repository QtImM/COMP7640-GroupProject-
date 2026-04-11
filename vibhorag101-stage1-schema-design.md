# 第一阶段设计：核心 Schema 重建与关键路由迁移规划

## 文档目的

这份文档用于推进 `vibhorag101/ECommerce-Grocery-Store` 的第一阶段改造工作。

第一阶段不直接追求把所有功能都写完，而是先把最关键的基础打稳：

- 按 COMP7640 题目要求重建核心数据库 schema
- 把命名从旧项目里的 `seller` 统一提升为 `vendor`
- 明确旧系统中哪些 Flask 路由需要迁移、重写或废弃
- 为后续实现 `multi-vendor order`、`transaction`、`tag search`、`order modification/cancellation` 打基础

## 第一阶段范围

### 包含

- 新核心表设计
- 主外键关系设计
- 关键业务关系设计
- 关键 Flask 路由迁移规划
- 第一阶段完成标准

### 不包含

- 页面美化
- 推荐算法实现
- 个性化界面优化
- `PyMySQL` 切换
- 全量旧功能迁移

## 设计原则

### 1. 完全贴合作业题目

新 schema 以题目要求为准，不再被旧项目的 grocery store 思路绑住。

### 2. 命名统一

数据库主体命名统一使用 `vendor`，不再继续沿用 `seller` 作为主概念。

### 3. 先把订单结构做对

后续几乎所有必做功能都依赖正确的订单结构，因此优先保证：

- 一个订单有多个订单项
- 一个订单可跨多个 vendor
- 一个订单可拆成多个 transaction
- 每个订单项有明确数量、单价、所属 vendor

### 4. 尽量让报告、ER 图、代码三者一致

后续设计应直接服务于：

- ER 图绘制
- relational schema 说明
- SQL 建表脚本
- Flask 代码实现
- presentation 讲解

## 新核心表设计

### 1. `vendor`

用于替代旧项目中的 `seller` 主体概念。

建议字段：

- `vendor_id` bigint primary key auto_increment
- `business_name` varchar(100) not null
- `contact_person` varchar(100) not null
- `email` varchar(100) not null unique
- `contact_number` varchar(30) not null
- `password_hash` varchar(255) not null
- `geographical_presence` varchar(255) not null
- `average_rating` decimal(3,2) default null
- `created_at` datetime not null
- `status` varchar(20) not null default 'active'

说明：

- `business_name` 对应题目里的 vendor business identity
- `geographical_presence` 用于承接题目要求里的地域信息
- `average_rating` 为后续 vendor 评价预留

### 2. `customer`

建议字段：

- `customer_id` bigint primary key auto_increment
- `full_name` varchar(100) not null
- `email` varchar(100) not null unique
- `contact_number` varchar(30) not null
- `shipping_address` varchar(255) not null
- `password_hash` varchar(255) not null
- `created_at` datetime not null
- `status` varchar(20) not null default 'active'

说明：

- 题目明确要求 customer 需要 contact number、shipping address、order history
- `order history` 通过 customer 和 orders 的关系自然体现

### 3. `product`

建议字段：

- `product_id` bigint primary key auto_increment
- `vendor_id` bigint not null
- `product_name` varchar(150) not null
- `listed_price` decimal(10,2) not null
- `stock_quantity` int not null
- `description` varchar(500) null
- `status` varchar(20) not null default 'active'
- `created_at` datetime not null
- foreign key (`vendor_id`) references `vendor`(`vendor_id`)

说明：

- `vendor_id` 直接绑定 product，前台更容易体现 marketplace 模型
- `stock_quantity` 是题目硬性要求
- 不再把 product 的归属放在 admin 上

### 4. `product_tag`

建议字段：

- `product_tag_id` bigint primary key auto_increment
- `product_id` bigint not null
- `tag_value` varchar(50) not null
- foreign key (`product_id`) references `product`(`product_id`)

约束建议：

- 每个 `product_id` 最多允许 3 条 tag 记录
- 应用层和数据库检查共同保证这个规则

说明：

- 采用关系表比固定 `tag1/tag2/tag3` 更干净
- 更适合做搜索

### 5. `orders`

建议字段：

- `order_id` bigint primary key auto_increment
- `customer_id` bigint not null
- `order_date` datetime not null
- `total_price` decimal(10,2) not null
- `status` varchar(20) not null
- `shipping_address` varchar(255) not null
- foreign key (`customer_id`) references `customer`(`customer_id`)

建议状态枚举：

- `placed`
- `processing`
- `shipped`
- `cancelled`
- `completed`

说明：

- 这是支持“发货前修改/取消”的关键基础

### 6. `order_item`

建议字段：

- `order_item_id` bigint primary key auto_increment
- `order_id` bigint not null
- `product_id` bigint not null
- `vendor_id` bigint not null
- `quantity` int not null
- `unit_price` decimal(10,2) not null
- `subtotal` decimal(10,2) not null
- `item_status` varchar(20) not null default 'placed'
- foreign key (`order_id`) references `orders`(`order_id`)
- foreign key (`product_id`) references `product`(`product_id`)
- foreign key (`vendor_id`) references `vendor`(`vendor_id`)

说明：

- 这是整个新模型最重要的表之一
- 订单项中显式保存 `vendor_id`，这样一个订单天然可跨多个 vendor
- `quantity` 和 `subtotal` 解决旧项目中“数量不落库”的问题

### 7. `transaction`

建议字段：

- `transaction_id` bigint primary key auto_increment
- `order_id` bigint not null
- `customer_id` bigint not null
- `vendor_id` bigint not null
- `amount` decimal(10,2) not null
- `payment_method` varchar(30) not null
- `transaction_time` datetime not null
- `transaction_status` varchar(20) not null default 'paid'
- foreign key (`order_id`) references `orders`(`order_id`)
- foreign key (`customer_id`) references `customer`(`customer_id`)
- foreign key (`vendor_id`) references `vendor`(`vendor_id`)

说明：

- 一个订单如果跨多个 vendor，可以生成多条 transaction
- 每条 transaction 对应 customer 向某个 vendor 的支付记录

## 关键业务关系

### 1. Vendor 与 Product

- 一个 vendor 可以拥有多个 product
- 一个 product 只能属于一个 vendor

### 2. Product 与 Tag

- 一个 product 最多有 3 个 tag
- 一个 tag 可以被多个 product 使用

### 3. Customer 与 Orders

- 一个 customer 可以创建多个 orders
- 一个 order 只属于一个 customer

### 4. Orders 与 Order Item

- 一个 order 包含多个 order_item
- 一个 order_item 只属于一个 order

### 5. Orders 与 Transaction

- 一个 order 可以对应多条 transaction
- 每条 transaction 对应一个 vendor

### 6. Multi-vendor Order

如果一个订单中包含：

- vendor A 的商品 2 件
- vendor B 的商品 3 件

那么数据库表现应为：

- `orders` 中 1 条订单主记录
- `order_item` 中多条商品记录，分别带不同的 `vendor_id`
- `transaction` 中至少 2 条记录，分别对应 vendor A 和 vendor B

## 为什么不继续沿用旧表

旧项目主要问题在于：

- `seller` 概念不够贴题
- `associated_with` 不能表达订单项数量
- `cart` 与订单的衔接依赖 Python 全局变量
- 没有 transaction 独立建模
- 没有 tags
- 没有明确 order status 生命周期

如果在旧表上继续修补，后续会越来越乱。

因此第一阶段采用“核心表干净重建”是更稳的路线。

## 关键路由迁移规划

下面是第一阶段需要重点规划的旧路由迁移关系。

### 1. 商品浏览

旧路由：

- `/home/<user_id>`

问题：

- 当前只是简单列 product
- 没有展示 vendor
- 没有 tag

新目标：

- 查询 `product + vendor + product_tag`
- 在页面上显示商品名称、价格、vendor 名称、库存、tags

处理建议：

- 保留旧入口语义
- 但内部查询逻辑完全换成新 schema

### 2. 商品搜索

旧项目：

- 没有正式搜索路由

新目标：

- 新增搜索接口
- 支持：
  - 商品名部分匹配
  - tag 匹配

处理建议：

- 新增独立搜索路由，而不是硬塞进旧逻辑

### 3. 加入购物车 / 准备下单

旧问题：

- 当前 heavily 依赖全局变量
- 商品数量不规范落库

新目标：

- 这一阶段先规划为“准备生成 order 草稿数据”
- 后续实现时可使用新的 cart / temporary order 方案

处理建议：

- 旧实现不要继续扩展
- 后续应围绕 `order_item` 重写

### 4. 创建订单

旧路由：

- `/order/<user_id>`
- `/placeOrder/<user_id>`

旧问题：

- 流程分散
- 数据落库依赖全局状态
- 无法清晰支持 multi-vendor

新目标：

- 创建 `orders`
- 批量写入 `order_item`
- 按 vendor 拆分并生成 `transaction`
- 同步更新库存

处理建议：

- 这两个旧路由后续建议重写，而不是局部修补

### 5. 修改订单

旧项目：

- 没有正式支持

新目标：

- 允许在 `placed` 或 `processing` 状态下删除某个 order_item
- 重新计算订单总价与 transaction 金额

处理建议：

- 新增独立路由

### 6. 取消订单

旧项目：

- 没有正式支持

新目标：

- 在订单尚未 `shipped` 时允许取消
- 更新 `orders.status = cancelled`
- 恢复库存

处理建议：

- 新增独立路由

### 7. Vendor 商品管理

旧路由：

- `/sell/<seller_id>`

旧问题：

- 逻辑仍然基于 seller
- 更像在旧 `sells` 关系里追加数据

新目标：

- 直接由 vendor 管理自己名下的 product
- 支持新增商品、更新库存、维护 tags

处理建议：

- 这个路由语义保留为 vendor dashboard 更合理
- 后续内部逻辑要改成以 `vendor_id` 为中心

## 旧表处理建议

第一阶段不要求立刻删除所有旧表，但建议分成三类：

### 1. 后续应废弃

- `seller`
- `sells`
- `associated_with`

### 2. 需要重构或替代

- `product`
- `orders`
- `customer`

### 3. 可暂时不动

- `admin`
- `offer`
- `delivery_boy`
- `product_feedback`

原因：

- 第一阶段先把和题目核心要求最直接相关的表做对
- delivery、offer、feedback 可放到后续再决定是否保留或重构

## 第一阶段完成标准

当下面这些都明确后，可以认为第一阶段设计完成：

- 新核心 schema 已经确定
- 表之间主外键关系已确定
- multi-vendor order 的数据表示方式已确定
- transaction 的建模方式已确定
- tags 的建模方式已确定
- 关键旧路由的迁移方向已确定

## 第二阶段建议切入点

第一阶段完成后，最合理的第二阶段实现顺序是：

1. 写新的 SQL schema
2. 实现 `vendor / product / product_tag`
3. 实现 `orders / order_item / transaction`
4. 实现搜索
5. 实现订单修改与取消

## 一句话结论

第一阶段的核心不是“修补旧项目”，而是先把这个项目从旧的 grocery-store 数据结构，升级成能真正承载 `multi-vendor marketplace` 的数据库骨架。
