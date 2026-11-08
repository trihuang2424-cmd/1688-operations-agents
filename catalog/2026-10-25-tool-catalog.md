# 1688 云端 MCP 工具目录

检查日期：2026-10-25（Asia/Shanghai）。实时目录：205 个工具，桥接器已开放全部 205 个。

范围：Accio 网关标记为 ali1688、server=accio 的工具。本文件来自实时工具元数据，不代表所有接口都已在当前店铺完成业务实测。工具包含卖家运营、买家采购、ERP 连接、生成任务及内部组件；并非每一个都是独立的店铺运营动作。

本次仅检查目录和参数定义，没有执行发布、改商品、客户触达、扣费生成或订单操作。

| 工具名 | 平台说明 |
|---|---|
| `1688_bp_inquiry_evaluate_sales_detail` | 1688商家业务员评估详情:查询指定业务员在指定日期范围内的询盘接待评估详情；调用前请先通过概览工具获取 saleIdentityId |
| `1688_bp_inquiry_evaluate_summary` | 1688商家业务员评估概览:查询指定日期范围内的业务员询盘接待评估概览，返回各业务员的服务评估、重点询盘和示例询盘；需要查看单个业务员详情时，请使用详情工具。 |
| `1688_factory_overview_imgs` | 工厂实力图:工厂实力图生成 |
| `1688_item_title_optimizer_interface` | [1688-item-title-optimizer]标题优化工具 |
| `1688_order_manger_summery` | 1688订单管家数据汇总:1688订单管家异常订单查询 |
| `1688_order_manger_urge` | 1688订单催发催揽 |
| `1688_procurement_digital_human_tool` | 1688云采数字员工执行工具:支撑1688云采数字员工运行的核心工具 |
| `1688_publish_category_page_info_query` | 1688类目查询信息接口:1688类目查询信息接口,用于商品发布时,查询类目下的页面信息 |
| `1688_publish_cpv_predict` | 1688cpv预测:基于商品同款等信息,预测商品的cpv |
| `1688_publish_image_classification` | AI发品图片分类接口:AI发品图片分类接口,输入图片list,对图片进行分类 |
| `1688_publish_material_package_generation` | 1688商品发布素材包生成:1688商品发布素材包生成,包括主图、标题、商品属性、产品规格、规格价格、规格库存、详情 |
| `1688_publish_product_draft_save` | 1688商品发布草稿:1688商品发布草稿,支持写入主图、标题、产品属性、产品规格、产品库存、产品价格、商品详情 |
| `1688_publish_sku_predict` | 1688sku预测:基于商品同款等信息,预测商品的sku |
| `1688_publish_title_prediction` | 1688标题预测工作流:1688标题预测工作流,基于同款等数据生成商品的标题 |
| `1688_query_shop_data` | 查询1688店铺数据:查询1688店铺数据，包含生意参谋、广告、评价、商品、物流履约等数据 |
| `1688_rag_query_api_info` | 1688自由取数接口RAG召回:通过自然语言召回相关的1688店铺数据的api接口和对应参数，然后再调用1688_query_shop_data即可获取相关数据 |
| `1688_refund_cancel` | 1688退款撤销 |
| `1688_refund_detail_new_query` | 1688新版退款单详情查询 |
| `1688_refund_list_query` | 1688退款列表查询 |
| `1688_source_suppliers` | 1688找供应商:根据行业词汇信息，寻找1688上的供货商信息。 |
| `1688_source_suppliers_infos` | 1688找供应商及详细信息:找供应商同时返回供应商的详细信息 |
| `a2a_501498_newton_buyer_script_generator` | 牛顿客户管理客群策略话术生成:牛顿客户管理的话术生成工具，针对需要触达的用户生成合适的话术，给商机做参考 |
| `addInvoiceTitle` | 新增发票抬头 |
| `address_gen` | 临时收货地址识别:根据用户输入的文本信息识别为临时收货地址 |
| `aegis_get_unique_id_by_user_id` | aegis根据userId获取唯一标识 |
| `aegis_register_profile` | Aegis Agent Profile 注册:注册 Aegis Agent Profile（幂等：INSERT ON DUPLICATE KEY UPDATE），支持 userId/agentId/deviceId/agentName/clientType/agentType/registerSource 参数 |
| `aegis_report_audit_log` | Aegis 意图审计上报:意图审计统一上报入口（CLI/SDK Step 0 / Step 1 均走此接口），支持 userId/agentId/intentProof/verifyResult/deviationResult/scene 等参数 |
| `ai_publish_by_imageurl` | 图片链接搜索类目信息和同款信息 |
| `ai_publish_excel_data_to_publish_url` | excel数据转成发品链接 |
| `ai_publish_image_to_publish_url` | ai发品单张图片生成发品链接:ai发品单张图片生成发品链接、支持图片base64字符串、支持任意一个可访问的公开图片链接 |
| `ai_publish_save_tair` | A发品存储页面缓存 |
| `ai_receptionist` | AI业务员 |
| `apply_dispute` | 申请投诉 |
| `batchApplyInvoice` | 批量开票申请:一次性集中申请多张票据开具 |
| `buyer_query_order_list` | 买家订单列表:查询买家订单列表 |
| `cancel_dispute` | 取消投诉 |
| `category_recognition_by_image_and_text` | 图片搜索文字搜索类目:图片搜索文字搜索类目,基于图片或者文字搜索类目,返回top3 |
| `cbu_501498_loginid_to_company` | 昵称查企:根据loginID去查公司名 |
| `cbu_image_analyse_tool` | 商品运营图片分析工具:商品运营图片分析工具,主要是分析图片用 |
| `cbu_image_generation_and_editing_tool` | 图片生成和图片编辑工具:支持文生、图生图等图片工具 |
| `cbu_offer_query_tool` | 查询商品基础信息工具:查询商品基础信息工具,目前仅查询标题和主图 |
| `cbu_skill_change_main_image` | 修改商品主图 |
| `cbu_skill_change_subject` | 修改商品标题 |
| `cha88_company_report_getReport` | AI企业背调-任务获取:获取异步提交的企业报告 |
| `cha88_company_report_submit` | AI企业背调-任务提交:提交AI企业背调任务 |
| `companySearch` | 公司搜索:基于公司名,品牌等检索公司 |
| `cowboy_daily_report` | cowboy_daily_report:查询指定日期的接待助手工作日报（接待数、转人工、转化等指标）。仅支持查询最近 30 天；超出范围返回参数错误。与 query_transfer_inquiries 区别：本工具返回聚合指标，后者返回询盘明细列表。 |
| `cowboy_knowledge_answer` | cowboy_knowledge_answer:为一条知识缺口记录补充标准答案并入库。须在用户复述问题+答案并明确确认后调用。写操作，以 recordId 幂等：同一 recordId 重复提交覆盖为最新答案。 |
| `cowboy_knowledge_query` | cowboy_knowledge_query:分页查询待完善的知识缺口列表（买家问过但接待助手答不上来的问题）。返回记录含 recordId，供 cowboy_knowledge_answer 补充答案使用。 |
| `cowboy_load_config` | cowboy_load_config:查询当前接待助手的配置与运行状态（是否激活、接待买家等级）。只读。身份由网关按会话上下文注入，无需任何入参。与 create/update/pause/resume 区别：本工具只读不写。 |
| `cowboy_test_chat` | cowboy_test_chat:以买家身份向待创建/已创建的接待助手发一句模拟提问，返回接待助手的回答（message）及动作（human=转人工 / ask=追问买家）。用于招聘 Step4 生成模拟对话预览，不产生真实买家会话。与 cowboy_load_config/create_cow_boy 区别：本工具只做问答模拟，不写配置。 |
| `create_cow_boy` | create_cow_boy:创建并激活 1688 AI 接待助手。仅用于招聘流程 Step4 用户明确确认后调用；调用前须已通过 cowboy_test_chat 完成模拟对话确认。写操作，非幂等：重复调用会重复创建，请勿在未确认失败原因时重试。身份由网关注入，无需传 sellerUserId。 |
| `csbc_ai_components_image_op_card` | 图片操作卡片 |
| `csbc_crm_customer_management` | 买家AI业务员 |
| `csbc_multi_shop_dashboard` | 店铺全景 |
| `customer_ai_profile` | 客户ai画像:客户ai画像查询&更新 |
| `customer_attr_add_column` | 新增一列自定义属性:描述：新增一列自定义属性。如果 attrKey 已存在且生效，则报错。成功后可选为指定买家批量填充初始值。<br>何时使用：当用户要求"新增一个字段"、"加一列信用分"、"创建自定义属性"时调用。 |
| `customer_attr_field_config` | 获取当前生效的自定义属性列表 + 可用于筛选的标签列表:描述：获取当前生效的自定义属性列表 + 可用于筛选的标签列表。合并返回，前端用于渲染筛选面板。<br>何时使用：当需要了解"可以用什么条件筛选客户"、"有哪些筛选维度"、"获取筛选配置"时调用。 |
| `customer_attr_list_all` | 查询商家所有自定义属性定义（含属性名 + 是否生效状态）:描述：查询商家所有自定义属性定义（含属性名 + 是否生效状态）。<br>何时使用：当用户询问"我有哪些自定义字段"、"查看属性列表"、"哪些字段是生效的"时调用。 |
| `customer_import` | 批量导入客户数据到 DB:描述：批量导入客户数据到 DB。如果买家记录不存在则新建，已存在则合并 extra_attrs（新值覆盖旧值）。<br>何时使用：当用户要求"导入客户"、"上传客户数据"、"新增一批客户"、"把这些客户信息写入系统"时调用。 |
| `customer_list` | 分页查询客户列表:描述：分页查询客户列表，支持多条件筛选、多字段排序、游标分页。基于 OpenSearch 实现毫秒级检索。<br>何时使用：当用户要求"查看客户列表"、"筛选杭州的VIP客户"、"按成交金额排序"、"找近30天采购金额超过1万的客户"等查询场景时调用。 |
| `customer_stats` | 获取客户统计指标（总客户数 + 近7天新增客户数）:描述：获取客户统计指标，仅返回汇总数（总客户数 + 近7天新增客户数）<br>前置条件：仅主账号可查全店汇总；子账号返回自己名下客户的汇总。<br>何时使用：当用户询问"我有多少客户"、"近期新增了多少客户"、"客户总数"等统计类问题时调用。<br>入参：无<br>示例响应：<br>{ "success": true, "data": { "totalCount": 12580, "recent7dNewCount": 23 } }<br>totalCount代表总个数，recent7dNewCount代表近7天新增个数<br> |
| `customer_tag_batch_apply` | 批量为客户打标签:描述：批量为客户打标签。如果标签在 tag_definition 中不存在，自动创建后再打标。<br>何时使用：当用户要求"给这些客户打上VIP标签"、"标记为高意向"、"批量打标"等调用。 |
| `deleteInvoiceTitle` | 删除发票抬头 |
| `distribute_offer` | 将商品铺货到下游:调用铺货接口，将商品铺货到下游平台 |
| `distribution_knowledge_tool` | 分销ai工作台知识查询tool |
| `distribution_offer_info` | 分销参谋数据 |
| `distribution_select_offer` | 分销选品:分销选品主接口 |
| `find_product` | 图文召回商品_正式版:支持query查找相关商品<br>支持输入图片搜索同款商品<br>支持输入1688商品ID搜索同款商品 |
| `fx_query_order` | 分销-订单查询 |
| `fx_send_ww` | 分销-发送旺旺 |
| `fx_ww_reply` | 分销-查询商家旺旺回复:查询商家回复记录 |
| `get_ad_channel_detail` | 【查询】广告渠道诊断数据:查询广告渠道诊断数据 |
| `get_channel_traffic` | 【查询】获取店铺各渠道的流量数据:获取指定日期店铺各渠道的流量数据 |
| `get_core_metrics` | [查询]店铺核心指标同行对比及趋势数据:查询店铺 7 项核心经营指标的本店值、同行同层平均值、评级，以及各指标的趋势对比数据 |
| `get_customer_profile` | [查询]客户画像数据:查询店铺客户画像数据，包括支付买家数、L会员买家数、客户数与同行优秀对比、回头率、新老客 GMV 构成、客单价等。 |
| `get_followup_record_by_buyer` | 查询买家跟进记录:获取买家近30天跟进记录，返回的是模型总结的结果，跟进记录包括：线上询盘、企微同步消息、客户计划执行 |
| `get_industry_benchmark` | 【查询】获取行业大盘流量数据:获取行业大盘流量数据，用于将店铺流量与行业整体水平对比，辅助诊断店铺流量异动。query_date 为查询日期（YYYY-MM-DD），一般传昨日；NEWTON_SHOP_LOGIN_ID 可选，不传默认当前店铺。 |
| `get_item_diagnosis_context` | 1688商品体检商品上下文 |
| `get_jky_auth_guide` | 获取吉客云授权状态:查询商家吉客云ERP授权状态。未授权或凭证无效时返回开通引导信息。执行任何吉客云数据查询前必须先调用本工具确认已授权。 |
| `get_jky_business_order` | 吉客云销售单查询（业务单）:通过 omsapi-business.order.get 查询吉客云销售单/业务订单。与 oms.trade.fullinfoget（get_jky_order）、脱敏版 jackyun.tradenotsensitiveinfos.list.get（get_jky_qimen_order）同属订单出口。 |
| `get_jky_order` | 获取吉客云销售订单:查询吉客云销售订单明细，支持按时间段、订单号、店铺等条件筛选。收件人姓名、手机号、地址等隐私字段已脱敏。 |
| `get_jky_qimen_order` | 吉客云销售单查询（奇门·脱敏定制）:通过奇门定制接口 jackyun.tradenotsensitiveinfos.list.get 查询销售单，收件人等敏感字段由服务端脱敏，与标准版 oms.trade.fullinfoget（get_jky_order）互补。 |
| `get_jky_warehouse` | 获取吉客云仓库信息:查询吉客云仓库列表及基础信息，包括仓库编号、名称、类型等。 |
| `get_jst_aftersale_received` | 获取聚水潭实际收货:查询售后退货入库的退仓单，跟踪退货收货进度与入库状态 |
| `get_jst_allocate` | 获取聚水潭调拨单:按时间或单号查询聚水潭 ERP 库存调拨单，含仓内与跨仓调拨 |
| `get_jst_inout` | 获取聚水潭其他出入库单:查询聚水潭 ERP 非订单出入库单，含盘盈、报损与领用等类型 |
| `get_jst_item_combine_sku` | 获取聚水潭组合商品:按 SKU 或时间查询聚水潭 ERP 组合装商品，含子 SKU 构成与数量 |
| `get_jst_item_inventory` | 获取聚水潭商品库存:按 SKU 或时间查询聚水潭 ERP 商品库存，含可用数、在途与锁定数 |
| `get_jst_item_sku` | 获取聚水潭商品SKU:按 SKU 编码或时间查询聚水潭 ERP 普通商品资料，含价格、供应商与标签 |
| `get_jst_item_skumap` | 获取聚水潭商品映射关系:按店铺 ID 查询聚水潭 ERP 店铺商品映射，含平台价格与上下架状态。前置条件：店铺需已完成聚水潭 ERP 授权，如未授权或授权失效时请先调用 get_jst_oauth_guide 获取开通引导。 |
| `get_jst_oauth_guide` | 获取聚水潭授权引导信息 |
| `get_jst_order` | 获取聚水潭订单:按时间或单号查询聚水潭 ERP 非淘系订单，含金额、收件人与明细 |
| `get_jst_out_order` | 获取聚水潭销售出库订单:按时间或单号查询聚水潭 ERP 销售出库单，含物流单号与明细 |
| `get_jst_purchase` | 获取聚水潭采购单:按时间或单号查询聚水潭 ERP 采购单，含入库进度与供应商信息 |
| `get_jst_qimen_item` | 获取聚水潭淘系商品资料:通过奇门接口查询淘系店铺商品资料，含上下架状态与平台售价。前置条件：店铺需已完成聚水潭 ERP 授权，如未授权或授权失效时请先调用 get_jst_oauth_guide 获取开通引导。 |
| `get_jst_qimen_order` | 获取聚水潭淘系订单:通过奇门接口查询淘系订单，含平台状态、物流与买家支付信息 |
| `get_jst_refund_order` | 获取聚水潭售后订单:按时间或单号查询聚水潭 ERP 售后单，含退款、换货与补发类型。前置条件：店铺需已完成聚水潭 ERP 授权，如未授权或授权失效时请先调用 get_jst_oauth_guide 获取开通引导。 |
| `get_jst_shops` | 获取聚水潭店铺:查询聚水潭 ERP 已启用店铺列表，返回店铺名称、平台与授权状态 |
| `get_jst_supplier` | 获取聚水潭供应商:按名称或编码分页查询聚水潭 ERP 供应商信息，含名称、分类与启用状态 |
| `get_jst_wms_partner` | 获取聚水潭仓库:查询聚水潭 ERP 已生效的分仓信息，含仓库名称与主仓标识 |
| `get_normalized_data` | 获取归一化数据 |
| `get_order_info_by_buyer` | 查询买家订单信息:获取买家近30天订单信息，包括1688站内和其他erp系统导入的订单数据 |
| `get_order_skills_config` | 获取下单技能配置 |
| `get_product_status` | 【查询】获取店铺商品状态数据:检查店铺商品搜索降权及下架状态。query_date 为查询日期（YYYY-MM-DD），一般传昨日；NEWTON_SHOP_LOGIN_ID 可选，不传默认当前店铺。前置条件：仅限已授权商家主子账号查询本店铺数据。 |
| `get_recommend_channel_detail` | 【查询】获取推荐渠道的诊断数据:获取推荐渠道流量的诊断数据，用于定位店铺推荐渠道流量异动原因，与 get_search_channel_detail（搜索渠道）配合按渠道下钻。query_date 为查询日期（YYYY-MM-DD），一般传昨日；NEWTON_SHOP_LOGIN_ID 可选，不传默认当前店铺。 |
| `get_search_channel_detail` | 【查询】获取搜索渠道的诊断数据:获取搜索渠道流量的诊断数据，用于定位店铺搜索渠道流量异动原因，与 get_recommend_channel_detail（推荐渠道）配合按渠道下钻。query_date 为查询日期（YYYY-MM-DD），一般传昨日；NEWTON_SHOP_LOGIN_ID 可选，不传默认当前店铺。 |
| `get_traffic_overview` | 【查询】获取全店流量概览数据:获取指定日期的全店流量概览数据 |
| `get_traffic_structure` | [查询]店铺流量结构数据:查询店铺流量来源排行、新老访客比、PC/无线占比、跳失率、入店搜索词等流量结构数据。 |
| `get_traffic_trend` | 【查询】获取逐日流量趋势数据:获取店铺逐日流量趋势 |
| `get_transaction_ranking` | [查询]行业交易排名数据:查询店铺在所属行业中的交易排名、排名百分位及 TOP 标杆数据。 |
| `image_agent` | 图像编辑Agent:针对商家的单图或者多图输入进行图像生成、编辑、美化操作。 |
| `image_bank_change_url_for_offer` | 外部商品图片改为商品可写入图片 |
| `image_bank_upload_picture` | 图片银行上传图片:基于base64上传图片工具 |
| `image_bank_url_external_to_internal` | 图片银行外部图片链接转1688站内图片 |
| `inquiry_data_load` | 询盘数据获取：【查询】通过商家ID、询盘买家索引序号和日期，来查询该商家在指定日期与特定买家的当日完整询盘对话。 |
| `jackyun_disconnect` | 吉客云-删除连接:断开用户与吉客云ERP的连接 |
| `jky_erp_get_sku_stock` | 获取吉客云分仓库存:按仓库查询SKU库存,含可用量、采购/调拨在途、多周期销量与成本,用于补货测算;warehouseCode与cols必填 |
| `jky_erp_get_stock_quantity` | 获取吉客云库存明细:按货品/批次/仓库查询库存数量、成本与效期,无必填,可选gmtModifiedStart/End |
| `jky_erp_get_stockin_doc` | 获取吉客云入库单:查询入库单,校准采购实际到货;字段参数名selelctFields(官方拼写),startDate/endDate必传 |
| `jky_erp_get_stockout_doc` | 获取吉客云出库单:查询出库单(inouttype=201为销售出库),字段参数名为selelctFields(官方拼写),startDate/endDate必传 |
| `jky_erp_get_vendor` | 获取吉客云供应商:查询供应商档案,含默认采购员、预付比例、是否支持代发,无必填 |
| `jky_erp_search_allocate` | 获取吉客云调拨单:按需查询调拨单(货品模式),cols必填,时间窗startCreateTime/endCreateTime |
| `jky_erp_search_goods_sku` | 获取吉客云货品资料:按条件查询货品档案,含默认供应商defaultVendId、分类、成本,无必填 |
| `jky_erp_search_purchase` | 获取吉客云采购单:查询采购单及在途/到货日,时间窗startModifyDate/endModifyDate;需商家先在吉客云后台订阅该接口 |
| `jushuitan_disconnect` | 聚水潭-删除连接:断开用户与聚水潭ERP的连接 |
| `leaderboard_tools` | 智能榜单系统工具:提供对应榜单查询 |
| `list_invoice_apply_records_by_page` | 分页查询发票申请记录 |
| `newton_ai_crm_customer_reach` | 牛顿AI CRM 客户触达:牛顿AI CRM 客户触达，支持根据AICRM里面的策略，对策略圈中的客户进行旺旺消息触达、优惠券发放、channel通知 |
| `newton_ai_crm_plan_operation` | 牛顿AI CRM 计划操作:客户管理场景客户触达计划操作，支持查询策略、修改策略状态、创建客户计划；修改策略前需先 根据planId查询；创建计划前需先圈选买家；权限：创建和调整仅主账号，子账号可查询 |
| `newton_bound_user_ids` | userId绑定列表查询:查询当前登录用户绑定且有管理权限的关联 user_id 列表；user_id 由源舟以 __userId__ 注入，不暴露给模型。 |
| `newton_im_card_get_layout_list` | IM卡片布局列表:获取IM卡片布局列表，支持按分组时间戳增量查询 |
| `newton_im_card_get_template_layouts` | IM卡片模板与布局查询:根据模板ID查询IM卡片模板及对应布局信息 |
| `newton_im_card_template_sync` | IM卡片模板同步:同步获取IM卡片模板列表，支持按时间戳增量分页查询 |
| `newton_im_file_try_upload` | IM文件预上传:获取 IM 文件 OSS 临时上传凭证，文件已存在时返回访问地址 |
| `newton_im_login_token_get` | 1688旺旺登录接口 |
| `newton_image_add_model_to_product` | newton_image_add_model_to_product:牛顿商品图加模特工具 |
| `newton_image_bg_change` | newton_image_bg_change:牛顿商品图片背景替换工具 |
| `newton_image_data_agent` | newton_image_data_agent:for newton*accio的image agent取数工具 |
| `newton_image_gen_carousel_images` | newton_image_gen_carousel_images:牛顿商品副图/详情图工具 |
| `newton_image_judge` | newton_image_judge:牛顿商品图片诊断分析工具 |
| `newton_offer_panorama_query_offer_diagnosis` | 牛顿商品库查询商品诊断:牛顿商品库-商品全景+明细：查询单个商品的 AI 诊断结果与一键优化行动点。前置：需已登录；店铺身份由网关注入。需先拿到 offer_id。 |
| `newton_same_competition_offer_compare_data` | 同款竞品商品对比数据:根据用户的商品id，查询top同款/竞品商品的数据，进行流量、价格、评价、商品属性对比 |
| `newton_shop_list_binds` | [查询]获取牛顿用户的多店铺绑定关系及AK |
| `newton_webim_im_chat_gateway_invoke` | WebIM网关invokeHsf:WebIM 的 ImChatGatewayHsfService.invokeHsf 网关服务，按 serviceName 路由到 IM 数据源并执行 |
| `offer_owner_query` | 商品归属查询:查询商品(Offer)归属与基础字段：入参 item_id，返回 offer 对象，含 userId(商品归属账号)、itemId、memberID、subject 等，用于商品归属校验。 |
| `offer_query_for_trade` | 商品sku和库存查询:根据offerId查询商品信息、sku、实时库存、起批量等交易条件、商品价格、区间价格、商品标等信息 |
| `offer_select_card` | 选择商品卡片 |
| `offer_sku_query_batch` | 批量商品SKU库存查询:根据多个商品id批量查询商品的offer和sku库存信息，每次调用支持最大50个商品id |
| `official_delivery_create_order` | 官方物流-预约上门取件:向物流服务商下单，预约上门取件 |
| `official_delivery_solution_query` | 官方物流-解决方案查询:根据收发地址，货品规格等信息提供可履约的物流商解决方案及报价 |
| `opp_market_search_data_query` | 遨虾-品类词市场数据搜索:查询相关品类词在指定电商市场的供需数据、销售趋势和 Google 搜索热度，适用于发现市场机会和评估品类词商业价值。 |
| `order_view` | 1688下单预览:根据用户ID、设备信息、业务身份、商品信息、采购数量、收货地址等采购要素完成下单前的预览和价格计算，同时支持指定是否使用红包、运费券等资产 |
| `parse_address` | 地址文本解析:将一段地址文本，解析成包含收件人、电话、行政区划和详细地址的结构化信息 |
| `pause_cow_boy` | pause_cow_boy:暂停已激活的接待助手，暂停后不再自动接待买家。需在用户明确确认后调用。与 resume_cow_boy 成对：pause 停止、resume 恢复。无需入参，身份由网关注入。写操作，以当前状态幂等。 |
| `product_cancel_offer` | 商品下架 |
| `product_repost_offer` | 上架商品 |
| `push_diagnosis_section` | 牛顿aw-mcpapp-商品诊断-数据 |
| `queryInvoiceTitlesByPage` | 分页查询发票抬头 |
| `querySellerInvoiceSettings` | 查询卖家开票设置 |
| `query_address_list` | 常用收货地址列表查询(脱敏版):根据用户userId查询常用收货地址列表（已脱敏） |
| `query_delivery_order_pack_list` | 订单查询运踪:根据1688订单id查询运踪 |
| `query_full_trace_list` | 运单号查询完整运踪:运单号查询完整运踪（需要运单号+收货人电话） |
| `query_invoice_amount` | 查询可开票金额:批量获取交易单可开票金额 |
| `query_order` | 订单查询:根据订单号查询订单详细信息 |
| `query_transfer_inquiries` | query_transfer_inquiries:分页查询指定日期转人工的买家询盘明细。仅支持最近 30 天。返回真实总数与明细，买家联系方式等敏感字段脱敏。 |
| `quotation_skill_get_detail` | 报价Skill-取已生效详情:查询商家已生效的报价方案（仅 status ∈ {normal,stop}），用于「查看历史已生效方案」这类只读场景。与 quotation_skill_load 区别：本工具不回落 draft、不自动创建，查不到已生效方案时返回空 data。返回 QuotationSkillDTO（含 技能状态 status、报价公式 config.quotationLogic、已上传材料清单 fileMap），结构同 quotation_skill_load。纯只读、幂等，可安全重试。身份由网关注入，无需任何入参。 |
| `quotation_skill_load` | 报价Skill-加载:加载商家可编辑的报价技能配置，是进入报价配置流程的入口必调工具。后端按网关注入的商家身份查 status ∈ {draft,normal,stop} 的任一记录返回；若都不存在则自动创建一条空 draft 后返回，因此本工具永不返回空。返回 QuotationSkillDTO（含 技能状态 status、报价公式 config.quotationLogic、已上传材料清单 fileMap）。与 quotation_skill_get_detail 区别：本工具会回落到 draft 且无记录时自动建草稿；quotation_skill_get_detail 只返回已生效的 normal/stop、查不到返回空。只读+可能建草稿，以商家身份幂等（重试只会拿到同一条 draft，不会重复创建）。身份由网关注入，无需任何入参。 |
| `quotation_skill_save` | 报价Skill-保存方案 :把商家确认的报价计算公式写入当前 draft 报价方案的 config.quotationLogic。仅用于报价配置流程 Step3 商家提交/修改公式并明确确认后调用；调用前须已通过 quotation_skill_load 确认存在 draft（无则 load 会自动建）。写操作、非幂等：每次全量覆盖旧的 quotationLogic（非 append），失败未查明原因前不要重试，以免覆盖商家已确认内容。后端按网关身份自动定位当前 draft，无需传 skillId。成功返回字符串 '保存成功'。身份由网关注入。 |
| `quotation_skill_simulate` | 报价Skill-模拟对话:模拟一段「买家询价 → 接待助手报价」的多轮完整对话，用于报价配置流程 Step4 让商家预览接待时的报价效果。后端自动从商家已上传的报价材料中挑选一个商品生成对话，不接受任何业务入参（不传 query / skillId，整段对话由后端生成）。返回 List<ConversationDTO>，每项 {query=买家提问, answer=接待助手回复（已渲染就绪）}。与 quotation_skill_load / save 区别：本工具只试算、不写库、不改配置。纯只读、可重试；因每次随机挑商品，多次调用返回的对话可能不同。返回可能含商品信息，买家/身份类字段由服务端脱敏。身份由网关注入。 |
| `resume_cow_boy` | resume_cow_boy:恢复被暂停的接待助手，恢复后继续自动接待。需在用户明确确认后调用。与 pause_cow_boy 成对。无需入参，身份由网关注入。写操作，以当前状态幂等。 |
| `same_img_offer_search` | 图搜同款 |
| `seller_activity_registered_info` | 【查询】商家近30天参与过的活动以及数据:查询近30天店铺活动参与及效果 |
| `seller_buyer_detail_hourly` | 买卖关系详细:买卖关系详细信息获取 |
| `seller_customer_business_province` | 【查询】客户地域分布（省份）:查询店铺的买家地域分布情况 |
| `seller_customer_detail` | 【查询】店铺商家客户明细列表:查询店铺客户明细列表，用于客户管理场景下查看客户支付金额、订单数、新老客结构等指标。orderBy 为必填排序字段（如 payAmt/payOrderCnt）；buyerType 可过滤新客/老客；NEWTON_SHOP_LOGIN_ID 可选，不传默认当前店铺。 |
| `seller_import_abnormal_offer` | 【查询】需要商家重点关注的异常商品（几个异常榜单取交集）:识别店铺异常商品列表 |
| `seller_top_offer` | 【查询】优秀商品列表:查询店铺优秀商品榜单（成交/流量/拉新/复购） |
| `seller_trade_code_index` | 【查询】商家店铺交易核心指标:查询店铺成交总盘核心指标，包含支付金额、买家数、转化率、客单价、新老客结构、退款金额及环比变化，用于健康度诊断，仅限已授权商家主子账号查询本店铺数据。 |
| `setDefaultInvoiceTitle` | 设置默认发票抬头 |
| `set_jky_credentials` | 录入吉客云凭证:录入商家吉客云自建应用的appkey和appSecret。商家需先在吉客云开放平台自建应用并订阅接口后获得这对凭证。凭证加密存储，不会回显。 |
| `set_jst_customer_id` | 设置聚水潭奇门路由客户ID:设置聚水潭奇门路由客户 ID。该 ID 决定 ERP 开放接口请求路由到哪个客户租户，仅在首次接入或更换客户时调用；配置错误会导致奇门查询（如 get_jst_qimen_item）失败，可重新调用本工具覆盖。customerId 必填，主子账号均可调用。 |
| `shop_and_tool_info` | 获取用户当前工具和店铺关系对:通过登录态获取用户的店铺和工具信息 |
| `skill_1688_item_select_get_item_detail` | [1688-item-select]商品评分与圈选服务 |
| `skill_1688_item_select_get_item_overview` | [1688-item-select]商品概览统计查询服务:[1688-item-select]商品概览统计查询服务。无入参，店铺身份由网关注入 |
| `skill_1688_item_select_get_shop_data` | [1688-item-select]店铺维度数据查询服务:[1688-item-select]店铺维度数据查询服务。无入参，店铺身份由网关注入 |
| `skill_1688_shop_daily_report_get_trade_data` | [1688-shop-daily-report]交易数据查询服务:[1688-shop-daily-report]获取指定日期的交易数据 |
| `skill_1688_shop_daily_report_get_traffic_data` | [1688-shop-daily-report]流量数据查询服务:[1688-shop-daily-report]获取指定日期的流量数据 |
| `skill_1688_shop_daily_report_get_user_data` | [1688-shop-daily-report]买家数据查询服务:[1688-shop-daily-report]获取指定日期的买家数据 |
| `tool_1688_knowledge_rag_query` | [查询]1688站内知识库RAG查询:通过输入自然语言，RAG查询1688站内知识库、学习中心内容 |
| `tool_business_analysis_query` | 经营分析数据查询:查询卖家经营分析基础版数据，包含资金分析、销售分析、商品排名、客户排名、区域分布等维度。入参：stat_period_value（统计周期，支持7/30/90天、yyyyMM月份、yyyyQN季度） |
| `tool_cpv_spi_before_check` | cpv商品属性修改预检查:检查商品属性是否可以修改。参数：item_id（商品ID）、prop_name（属性名称）、prop_value（属性值）。返回检查结果，如果没有权限会提示没有权限。 |
| `tool_cpv_spi_execute` | cpv商品属性修改执行:执行商品属性修改操作。参数：item_id（商品ID）、prop_name（属性名称）、prop_value（属性值）。需要先调用tool_cpv_spi_before_check进行修改前校验，再调用该接口执行实际修改，如果没有权限会提示没权限。 |
| `tool_get_offer_login_id` | 根据offerId查询商品所属loginId:根据商品offerId查询该商品所属的卖家loginId（即NEWTON_SHOP_LOGIN_ID），用于后续工具调用时作为店铺标识传入 |
| `tool_one_click_spi_before_check` | [执行]一键执行前置检查:用于在一键执行前做前置检查 |
| `tool_one_click_spi_execute` | [执行]一键执行操作:[执行]商品执行操作接口，可以修改标题、图片、库存、打折、发会员号动态；使用前需要调用tool_one_click_spi_before_check来进行权限检查，通过后才可以继续使用该工具执行操作； |
| `tool_search_offer_by_keyword` | 通过关键词搜索店铺商品:在当前登录店铺内按关键词搜索商品，用于用户未给商品 ID、但描述了目标商品特征时定位候选。返回列表体积较大，请用 page_size 控制条数。 |
| `tool_shop_health_check` | 店铺健康检查:店铺健康聚合查询，按 code 分三次调用：order_risk（订单履约）、shop_punish（合规扣分）、feedback（买家评价） |
| `updateInvoiceTitle` | 修改发票抬头 |
| `update_cowboy_config` | update_cowboy_config:更新已激活接待助手的接待买家等级范围。需在用户明确确认后调用；完成后建议用 cowboy_load_config 回读校验。身份由网关注入。 |
| `view_apply_dispute` | 查看申请投诉 |
| `view_dispute_detail` | 查看投诉详情 |
| `xiaobangbang_bind_connection` | 销帮帮-执行连接:保存销帮帮授权信息，完成应用连接 |
| `xiaobangbang_disconnect` | 销帮帮-删除连接:断开用户与销帮帮应用的连接 |
| `xiaobangbang_query_connection` | 销帮帮-查询连接状态:查询用户与销帮帮应用的连接状态 |

