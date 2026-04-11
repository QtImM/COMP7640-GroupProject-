# vibhorag101/ECommerce-Grocery-Store 项目需求差距分析

## 分析对象

- 仓库：`vibhorag101/ECommerce-Grocery-Store`
- 本地路径：`C:\Users\Tim\Desktop\7640 Group Project\ECommerce-Grocery-Store`
- 分析日期：`2026-04-11`

## 这个项目目前已经有的内容

### 1. 技术路线与课程要求比较接近

- 项目使用的是 `Python + Flask + MySQL`，整体方向和你们作业要求的 `Python + MySQL` 比较接近。
- 它是一个可运行的网页界面项目，符合题目里“CLI 或 GUI 都可以”的要求。
- `README.md` 里已经给出了基本运行说明。
- 仓库里自带 `Dump.sql`，方便恢复数据库和理解表结构。

### 2. 它已经具备很强的“数据库课程项目材料”

- 有 ER 图：`Submit/ER Diagram Final.pdf`
- 有关系模式图：`Submit/Relationship Schema.pdf`
- 有项目报告：`Submit/Project Report.pdf`
- 还有比较完整的数据库提交材料，例如：
  - `Dump.sql`
  - `Submit/Dump.sql`
  - `Submit/createIndex.sql`
  - `Submit/finaltriggers.txt`
  - `Submit/SQL_Queries/*.sql`
  - `Submit/Grants/*.txt`

这说明它非常适合被当作数据库课程项目的参考骨架，尤其适合参考报告结构、演示结构和 SQL 提交形式。

### 3. 核心电商实体已经比较完整

从 `Dump.sql` 看，这个项目已经有以下核心表：

- `seller`
- `customer`
- `product`
- `orders`
- `cart`
- `offer`
- `category`
- `delivery_boy`
- `product_feedback`
- 以及若干关系表，例如：
  - `sells`
  - `associated_with`
  - `selects`
  - `rates_order_delivery`
  - `admin_views`

这意味着它已经完成了相当一部分数据库建模工作。

### 4. 已经实现了不少基础业务流程

从 `market/routes.py` 可以看出，这个项目已经支持：

- customer 注册与登录
- seller 注册与登录
- admin 注册与登录
- 浏览商品
- 将商品加入购物车
- 下单
- 使用优惠码 / offer
- admin 添加 seller
- admin 添加 product
- admin 添加 delivery boy
- admin 查看订单
- seller 通过 `sells` 关系维护自己卖的商品

所以它不是只有数据库没有功能，而是已经具备了一个基础可运行的电商流程。

### 5. 在数据库层面已经具备多 seller 支持

- 仓库中有 `seller` 表。
- `sells` 表把 seller 和 product 关联起来，支持 seller 与 product 的多对多关系。
- README 和关系设计里也明确区分了 seller / customer / admin 角色。

因此，这个项目并不是纯单店铺模型，它已经具备“多卖家”雏形。

## 这个项目还缺什么，或者和你们 COMP7640 题目不一致的地方

### 1. Vendor profile 只覆盖了一部分

课程要求里，每个 vendor 应该有：

- vendor ID
- business name
- average rating from customers
- geographical presence
- inventory of products

当前项目的情况：

- `seller` 表已经有 ID、姓名、联系方式、经营地点
- 商品库存关系可以通过 `sells` 看出
- 但是没有清晰的 vendor 平均评分机制
- 也没有特别明确、面向 marketplace 的 `business name` 设计

差距：

- 你们还需要把 `vendor profile` 设计得更完整、更贴近题目描述。

### 2. Product 模型和题目要求不一致

课程要求里，每个 product 需要有：

- 唯一 product ID
- 名称
- 标价
- stock quantity
- 最多 3 个 tags

当前项目的情况：

- `product` 表有 ID、名称、价格、品牌、规格、单位、分类、admin 外键
- 但没有 `stock quantity`
- 没有 `tag`
- 也没有“最多 3 个 tag”的约束设计

差距：

- 你们必须重新扩展 product 模型，补上库存和 tags。

### 3. 没有实现按 tag 或部分名称搜索商品

题目要求中明确写了：

- 用户应能通过 tag 发现商品
- 搜索应返回 tag 命中，或者商品名部分匹配，或者关联 tag 匹配的商品

当前项目的情况：

- 现有页面主要是商品展示和购物流程
- `market/routes.py` 里没有 tag 搜索逻辑
- `Dump.sql` 里也没有 tag 相关表或字段

差距：

- 这是当前项目缺失最明显的必做功能之一。

### 4. 没有把 transaction 作为独立核心实体建模

课程要求里明确提到了 transaction，它应该和以下内容关联：

- customer 的 order
- customer 到 vendor 的 payment
- 至少一个来自该 vendor 的 product

当前项目的情况：

- 有 `orders` 表，也有支付方式字段
- 但没有单独的 `transaction` 表
- 支付只是在 order 层面记录，没有细化到 vendor 级别

差距：

- 如果你们想更严格贴合作业要求，就需要设计一张明确的 `transaction` 表。

### 5. “单个订单可跨多个 vendor”没有被清晰实现

题目明确要求：

- 一个订单可以包含跨多个 vendor 的交易

当前项目的情况：

- 现有 schema 有 `orders`、`cart`、`associated_with`、`sells`
- 但没有清楚记录：
  - 某个订单中的某个商品由哪个 vendor 提供
  - 这个订单里每种商品的数量是多少
  - 一个订单中多个 vendor 各自对应哪些商品

差距：

- 这是和题目之间的一个重大不一致点。
- 你们大概率需要增加 `order_item` 之类的表，以及和 vendor 绑定的 transaction 设计。

### 6. 订单中“每个商品的数量”没有正确落库

课程要求里，订单应该记录：

- 商品列表
- 每种商品的数量

当前项目的情况：

- `associated_with(Customer_ID,Cart_ID,Product_ID)` 只记录了 customer、cart、product 的关系
- 没有 quantity 字段
- Python 代码里主要是把商品临时放在内存列表里，并在全局变量中统计总数

差距：

- 每个订单项的数量并没有被规范地存到数据库里。

### 7. 没有实现“发货前修改订单 / 取消订单”

题目要求中明确写了：

- 用户可以删除订单中的某些商品
- 或者在发货前取消整个订单

当前项目的情况：

- 现在支持“加购物车”和“提交订单”
- 但没有清晰的路由或逻辑支持：
  - 对已下单订单进行修改
  - 删除某个订单项
  - 取消整个订单
- 同时，系统里也没有成熟的 shipping 状态流转逻辑

差距：

- 这是另一个当前缺失的重要必做功能。

### 8. Order status 和题目要求不一致

题目要求每个订单应有状态字段。

当前项目的情况：

- `orders` 表里有支付方式、金额、地址、日期、时间、delivery boy
- 但在实际 SQL schema 里没有明确的 `status` 字段
- 无法很好表示例如：
  - placed
  - processing
  - shipped
  - cancelled

差距：

- 你们需要增加订单状态字段，并围绕它定义业务规则。

### 9. 项目更像 grocery store，而不是题目要求的 marketplace

当前项目的定位：

- 一个在线杂货电商系统
- 有 admin、seller、customer、delivery boy 等角色

差距：

- 你们题目强调的是 `multi-vendor marketplace with personalized user experiences`
- 这个仓库虽然有 seller，但整体叙事更偏 grocery store
- “personalized user experience” 在当前实现里也不明显

具体影响：

- 如果直接沿用这个项目的业务包装，你们在报告和展示时会比较难说明“为什么这是一个多 vendor marketplace”，因为现在的核心体验更像一个统一运营的杂货商城。
- 题目强调的是“平台”视角，也就是多个 vendor 在同一个 marketplace 内共存；但当前项目里 seller 虽然存在，前台用户视角并没有明显看到“这是不同 vendor 提供的商品”。
- 题目还强调 `personalized user experiences`，而当前系统没有明显的个性化功能，例如：
  - 基于历史订单的推荐
  - 按用户偏好展示商品
  - 按地区、评分、标签筛选 vendor 或 product

建议如何调整：

- 在系统叙事上，把项目从“online grocery store”改成“multi-vendor grocery marketplace”。
- 在数据层面强化 vendor 的存在感，例如：
  - 每个商品展示 vendor 名称
  - vendor 有独立主页或 profile
  - 用户可以按 vendor 浏览商品
- 在功能层面至少补一个轻量级个性化功能，避免“personalized user experiences”完全停留在口头描述。比较适合课程项目的选择有：
  - 根据用户历史购买的 category 或 tag，优先展示相关商品
  - 展示“你可能还想买”的推荐区
  - 根据用户配送地区优先展示本地 vendor

建议优先级：

- 最低要求：把项目包装和界面叙事改成 marketplace，并明确显示 vendor 信息
- 更稳妥的做法：再补一个简单但可演示的 personalization 功能

结论：

- 第 9 点不一定要求你们重写整个系统，但至少要把“单店杂货站”改造成“多 vendor 平台”的表达方式，并补一个能够讲得出口的个性化体验点。

### 10. 数据库连接库和 PDF 指定的不完全一致

PDF 中提到 Python 方案建议使用 `PyMySQL`。

当前项目的情况：

- 项目使用的是 `flask_mysqldb`

差距：

- 功能上问题不大，但如果老师对实现要求非常严格，你们最好考虑是否改成 `PyMySQL`，或者至少准备好解释理由。

具体影响：

- 从“能不能连上 MySQL”这个角度看，`flask_mysqldb` 没问题，项目也确实已经正常按 MySQL 方式组织。
- 但如果老师是严格按 PDF 里写的技术点来检查，可能会问为什么没有直接使用 `PyMySQL`。
- 这类问题通常不会影响你们的业务逻辑设计，但可能影响“是否严格按题目要求实现”的说服力。

我对这一点的判断：

- 这是一个中低优先级问题，不像 `tag search`、`transaction`、`order modification` 那样属于核心功能缺失。
- 如果你们时间紧，优先补功能，不一定要第一时间改数据库连接库。
- 如果你们希望项目更稳、更贴题，后面把数据库访问层改成 `PyMySQL` 会更保险。

建议方案：

- 方案 A：先不改，继续沿用 `flask_mysqldb`
  - 优点：改动最小，不影响当前分析和后续重构
  - 缺点：如果老师较严格，需要在报告里解释“虽然连接库不同，但仍然是 Python 访问 MySQL”
- 方案 B：后续切换到 `PyMySQL`
  - 优点：和 PDF 表述更一致，答辩时更好解释
  - 缺点：需要改初始化、查询调用方式，以及部分数据库访问代码

当前建议：

- 先把它记为“需要决定但不急着立刻处理”的技术差异。
- 在你们开始真正改代码前，再统一决定是否把 `flask_mysqldb` 切换为 `PyMySQL`。

结论：

- 第 10 点不是当前最大的 blocker。
- 它更像一个“规范贴合度”问题，而不是“系统做不出来”的问题。
- 相比之下，功能层面缺失的第 3、4、5、6、7、8 点优先级更高。

## 额外需要注意的技术问题

这些不一定直接违反作业要求，但如果你们要在这个项目基础上继续开发，会比较关键。

### 1. 购物车状态保存在 Python 全局变量里

`market/routes.py` 里用了这些全局变量：

- `cart_id`
- `total_val`
- `total_count`
- `customer_cart_list`

这对多用户系统来说很脆弱，因为不同用户之间可能互相污染状态。

### 2. 购物车和数量逻辑不够规范

- cart item 没有按规范方式存储数量
- 下单过程部分依赖 Python 内存状态，而不是完整依赖数据库
- 这会让后续补“订单修改”“数量调整”“跨 vendor 订单”时变得比较困难

### 3. 登录和安全实现比较简单

- 密码看起来是明文存储
- 登录时是先查整张表，再在 Python 里循环匹配

对于课程原型来说还能接受，但从实现质量上说不算理想。

## 总体判断

这个仓库很适合用来参考以下内容：

- ER 图思路
- 关系模式设计思路
- 报告结构
- MySQL dump 和 SQL 提交形式
- seller / customer / admin 的角色拆分
- 基础的 product-cart-order 流程

但是，它 **还不能直接完整满足** 你们的 COMP7640 项目要求。

当前最主要的缺口有：

1. vendor profile 不够完整
2. 没有 stock quantity
3. 没有 product tags
4. 没有 tag / partial-name search
5. 没有显式 transaction 建模
6. 没有清晰支持多 vendor 单订单
7. 没有把订单项数量正确存库
8. 没有订单修改 / 取消功能
9. 没有完整的 order status 生命周期

## 建议

这个仓库最适合的定位是：

- 作为你们项目的 **参考骨架**
- 而不是直接作为最终答案

最值得借鉴的部分：

- 项目整体结构
- Flask + MySQL 的基础搭建方式
- 多角色流程
- SQL 提交材料组织方式
- ER 图 / 报告 / 演示材料结构

最需要你们自己重做的部分：

- vendor profile
- product schema
- order 与 order item schema
- transaction schema
- search 功能
- order modification / cancellation 流程

## 建议的下一步

最合理的做法是：

- 保留这个仓库作为参考
- 然后基于你们题目，重新设计自己的核心 schema

建议重点围绕这些表重构：

- `vendor`
- `product`
- `product_tag` 或固定 3 个 tag 字段
- `customer`
- `orders`
- `order_item`
- `transaction`

然后再按你们自己的 schema 去调整 Flask 路由和功能实现。
