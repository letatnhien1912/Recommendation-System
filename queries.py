cross_sell_rec_all_customer = """select top 10 a.ProductId item_1,
        b.ProductId item_2,
        count(*) times_bought_together
    from OrdersItem a
    join OrdersItem b on a.OrdersId = b.OrdersId
    join Product pro on b.ProductId = pro.Id
    where a.ProductId <> b.ProductId
        and a.ProductId = {ProductId}
        and pro.Active = 1
    group by a.ProductId, b.ProductId
    order by times_bought_together desc"""

cross_sell_rec = """WITH
        item_procat
        AS
        (
            SELECT
                ord.CustomerId,
                item.Id itemId,
                item.OrdersId,
                item.ProductId,
                IIF(procat.ParentId IS NULL, procat.Id, procat.ParentId) CategoryId
            FROM OrdersItem item
                JOIN Orders ord ON item.OrdersId = ord.Id
                JOIN Product pro ON item.ProductId = pro.Id
                JOIN ProductCategory procat ON pro.CategoryId = procat.Id
            WHERE ord.StatusId = 10
                AND ord.CustomerId IS NOT NULL
                AND item.ProductId IS NOT NULL
        )
    ,
        pairCat
        AS
        (
            SELECT
                distinct
                a.CustomerId,
                a.OrdersId,
                case when a.ProductId > b.ProductId then CONCAT(b.ProductId, '|', a.ProductId) else CONCAT(a.ProductId, '|', b.ProductId) end ProductPair,
                case when a.CategoryId >= b.CategoryId then CONCAT(b.CategoryId, '|', a.CategoryId) else CONCAT(a.CategoryId, '|', b.CategoryId) end CatPair,
                case when a.CategoryId >= b.CategoryId then b.CategoryId else a.CategoryId end cat_1,
                case when a.CategoryId >= b.CategoryId then a.CategoryId else b.CategoryId end cat_2
            FROM item_procat a
                JOIN item_procat b ON a.OrdersId = b.OrdersId
            WHERE a.ProductId <> b.ProductId
                AND a.CustomerId = {CustomerId} -- REPLACE BY CUSTOMER ID
        )
    ,
        pairCat_ranking
        AS
        (
            SELECT DISTINCT CatPair,
                COUNT(*) OVER (PARTITION BY CatPair) PairCount,
                (COUNT(*) OVER (PARTITION BY CatPair))*1.0 / COUNT(*) OVER () Contribution
            FROM pairCat
        )
    ,
        pairProduct
        AS
        (
            SELECT a.ProductId item_1, b.ProductId item_2, COUNT(*) PairCount,
                case when a.CategoryId >= b.CategoryId then CONCAT(b.CategoryId, '|', a.CategoryId) else CONCAT(a.CategoryId, '|', b.CategoryId) end CatPair
            FROM item_procat a
                JOIN item_procat b ON a.OrdersId = b.OrdersId
                JOIN Product pro ON b.ProductId = pro.Id
            WHERE a.ProductId <> b.ProductId
                AND a.ProductId = {ProductId} -- REPLACE BY PRODUCT ID
                AND pro.Active = 1
            GROUP BY a.ProductId, a.CategoryId, b.ProductId, b.CategoryId
        )
    ,
        top10_count
        AS
        (
            SELECT TOP 10
                p1.*, p2.Contribution
            FROM pairProduct p1 LEFT JOIN pairCat_ranking p2 ON p1.CatPair = p2.CatPair
            ORDER BY p1.PairCount DESC
        )
    SELECT *
    FROM top10_count
    ORDER BY Contribution DESC, PairCount DESC"""

recsys_dataset_refresh = """WITH facebook_preference AS (
        SELECT facebooklog.UserId CustomerId, facebooklog.Item action_type, facebookproduct.SubId ProductId,
            IIF(facebooklog.Item = 'reaction', 
                IIF(facebooklog.ReactionType IN ('like','wow','care','love'), 1, 0),
            IIF(facebooklog.Item = 'share', 4, 
            IIF(facebooklog.Item = 'comment'
                AND facebooklog.Intent IN ('GetFit','GetProductInfo','AddCart',
                'HoldCart','ConfirmOrder','CheckoutCart','GetImage'), 3, 0)        
                )) preference_score,
            DATEDIFF(DAY, facebooklog.DateInserted, GETDATE()) recency
        FROM FacebookLogActivity facebooklog
            JOIN FacebookPostProduct facebookproduct ON facebooklog.PostId = facebookproduct.MainId
            JOIN Customer cus ON facebooklog.UserId = cus.Id
        WHERE facebooklog.Verb = 'add'
            AND facebooklog.UserId is not null
            AND facebooklog.Item IN ('reaction','share','comment')),

    order_preference AS (
        SELECT CustomerId, item.ProductId,
            IIF(StatusId = 10, 'purchase',
            IIF(IsAddCart = 1, 'addtocart', null)) action_type,
            (IIF(StatusId = 10, 7,
            IIF(IsAddCart = 1, 5, 0)) * Quantity) preference_score,
            DATEDIFF(day,item.CreateTime,GETDATE()) recency
        FROM Orders ord
            JOIN OrdersItem item ON ord.Id = item.OrdersId
        WHERE CustomerId is not null)

    SELECT CustomerId, ProductId, action_type, preference_score, recency FROM facebook_preference WHERE preference_score > 0
    UNION
    SELECT CustomerId, ProductId, action_type, preference_score, recency FROM order_preference WHERE preference_score > 0"""

recsys_product_preference = """WITH facebook_preference AS (
        SELECT facebookproduct.SubId ProductId,
            IIF(facebooklog.Item = 'reaction', 
                IIF(facebooklog.ReactionType IN ('like','wow','care','love'), 1, 0),
            IIF(facebooklog.Item = 'share', 4, 
            IIF(facebooklog.Item = 'comment'
                AND facebooklog.Intent IN ('GetFit','GetProductInfo','AddCart',
                'HoldCart','ConfirmOrder','CheckoutCart','GetImage'), 3, 0)        
                )) preference_score,
            DATEDIFF(DAY, facebooklog.DateInserted, GETDATE()) recency
        FROM FacebookLogActivity facebooklog
            JOIN FacebookPostProduct facebookproduct ON facebooklog.PostId = facebookproduct.MainId
        WHERE facebooklog.Verb = 'add'
            AND facebooklog.Item IN ('reaction','share','comment')),

order_preference AS (
    SELECT item.ProductId,
        (IIF(StatusId = 10, 7,
        IIF(IsAddCart = 1, 5, 0)) * Quantity) preference_score,
        DATEDIFF(day,item.CreateTime,GETDATE()) recency
    FROM Orders ord
        JOIN OrdersItem item ON ord.Id = item.OrdersId)

, preference AS (SELECT ProductId, preference_score, recency FROM facebook_preference WHERE preference_score > 0
UNION
SELECT ProductId, preference_score, recency FROM order_preference WHERE preference_score > 0)

SELECT pre.*, pro.CategoryId
FROM preference pre
JOIN Product pro ON pre.ProductId = pro.Id"""

recsys_product_dataset = """select pro.Id productId, pro.NameUniCode productName, STRING_AGG(Tag.NameUnicode, '|') tag, pro.Active, proquant.Quantity
from ProductTags protag
    join Tags tag on protag.SubId = tag.Id
    right join Product pro on protag.MainId = pro.Id
    right join (
        select ProductId, sum(Quantity) Quantity from ProductColor group by ProductId
    ) as proquant on pro.Id = proquant.ProductId
group by pro.Id, pro.NameUniCode, pro.Active, proquant.Quantity"""

recsys_purchase_dataset = """select distinct CustomerId, ProductId
    from OrdersItem item
        join Orders ord on item.OrdersId = ord.Id
    where StatusId = 10
        and CustomerId is not null
        and ProductId is not null"""

recsys_tag_dataset = "select Id, NameUnicode from Tags"

recsys_cookie_dataset = """with a as (
    select GuestId CookieId, RefId ProductId, Count ViewCount, DATEDIFF(DAY, sta.CreateTime, GETDATE()) recency
    from StatisticRef sta
    join Product pro on sta.RefId = pro.Id
    where GuestId is not null
        and GuestId like 'SS_%'
),

lastest_record as (
    select GuestId CookieId, max(CreateTime) lastest_date
    from StatisticRef
        where GuestId is not null
            and GuestId like 'SS_%'
    group by GuestId
)

select a.CookieId, a.ProductId, SUM((1 - (recency*1.0 / b.max_recency)) * ViewCount) preference_score
from a
join lastest_record c on a.CookieId = c.CookieId,
(select max(recency) max_recency from a) as b
where c.lastest_date >= DATEADD(MONTH, -6, GETDATE())
group by a.CookieId, a.ProductId"""
