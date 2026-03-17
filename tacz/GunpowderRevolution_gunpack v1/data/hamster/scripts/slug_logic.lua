local M = {}

-- 自定义的散步函数，返回一对坐标{x, y}，代表子弹以准心为原点，平行于屏幕平面8格外的落点
-- 下面是一个参考，子弹将以一个半径为1的圆形均匀分布
function M.calcSpread(api, ammoCnt, basicInaccuracy)
    if (api:getFireMode() == SEMI) then
        if (api:getAimingProgress() > 0.8) then
            return {0, 0}
        else
            math.randomseed(api:getCurrentTimestamp())
            local x = (math.random() - 0.5) * basicInaccuracy * 0.4
            local y = (math.random() - 0.5) * basicInaccuracy * 0.4
            return {x, y}
        end
    end
end

return M