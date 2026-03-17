local default = require("hamster_hamster_state_machine")
local GUN_KICK_TRACK_LINE = default.GUN_KICK_TRACK_LINE

local STATIC_TRACK_LINE = default.STATIC_TRACK_LINE
local BLENDING_TRACK_LINE = default.BLENDING_TRACK_LINE

local MAIN_TRACK = default.MAIN_TRACK
local ADS_TRACK = default.ADS_TRACK
local BULLET_TRACK = default.BULLET_TRACK
local BOLT_CAUGHT_TRACK = default.BOLT_CAUGHT_TRACK

local bolt_caught_states = default.bolt_caught_states
local main_track_states = default.main_track_states
local ADS_states = default.ADS_states

local normal_states = setmetatable({
    bulletcount = 100
}, {__index = bolt_caught_states.normal})
local caught_states = setmetatable({}, {__index = bolt_caught_states.bolt_caught})

local gun_kick_state = setmetatable({}, {__index = default.gun_kick_state})
local aiming = setmetatable({}, {__index = ADS_states.aiming})
local idle_state = setmetatable({
    empty = -1
}, {__index = main_track_states.idle})

local function isNoAmmo(context)
    -- 这里同时检查了枪管和弹匣
    return (not context:hasBulletInBarrel()) and (context:getAmmoCount() <= 0)
end

function gun_kick_state.transition(this, context, input)
    if (input == INPUT_SHOOT) then
        local track = context:findIdleTrack(GUN_KICK_TRACK_LINE, false)
        local last_shoot_timestamp = context:getLastShootTimestamp()
        local current_timestamp = context:getCurrentTimestamp()
        local shoot_interval = context:getShootInterval()
        if (current_timestamp - last_shoot_timestamp < shoot_interval + 100) then
            if (context:isCrawl()) then
                context:runAnimation("shoot_bipod", track, true, PLAY_ONCE_STOP, 0)
            else
                context:runAnimation("shoot_auto", track, true, PLAY_ONCE_STOP, 0)
            end
        else
            context:runAnimation("shoot", track, true, PLAY_ONCE_STOP, 0)
        end
    end
    return nil
end

function normal_states.entry(this, context)
    context:runAnimation("bullet_state", context:getTrack(BLENDING_TRACK_LINE, BULLET_TRACK), true, PLAY_ONCE_STOP, 0)
    return this.bolt_caught_states.normal
end


function normal_states.update(this, context)
    if (isNoAmmo(context)) then
        context:trigger(this.INPUT_BOLT_CAUGHT)
    end
    local a = 15
    local c = 11
    local b = context:getMaxAmmoCount() - c

    if (idle_state.empty ~= -1 and context:getCurrentTimestamp() > idle_state.empty + 5600) then
        context:setAnimationProgress(context:getTrack(BLENDING_TRACK_LINE, BULLET_TRACK), 1.6, false)
        if (normal_states.bulletcount < context:getAmmoCount()) then
            idle_state.empty = -1
        end
    else
        if (context:getMaxAmmoCount() - context:getAmmoCount() < a) then
            context:setAnimationProgress(context:getTrack(BLENDING_TRACK_LINE, BULLET_TRACK), 1.6 - ((context:getMaxAmmoCount() - context:getAmmoCount()) * 0.1), false)
        elseif (context:getAmmoCount() <= c) then
            context:setAnimationProgress(context:getTrack(BLENDING_TRACK_LINE, BULLET_TRACK), 2.6 + ((c - context:getAmmoCount()) * 0.1), false)
        else
            context:setAnimationProgress(context:getTrack(BLENDING_TRACK_LINE, BULLET_TRACK), 1.7 + (1 - context:getAmmoCount()/context:getMaxAmmoCount()), false)
        end
    end
    normal_states.bulletcount = context:getAmmoCount()
end

function caught_states.update(this, context)
    if (not isNoAmmo(context)) then
        context:trigger(this.INPUT_BOLT_NORMAL)
    end
end

-- 进入瞄准状态
function aiming.entry(this, context)
    -- 开始瞄准时播放瞄准动画，并且将其挂起
    local track = context:getTrack(BLENDING_TRACK_LINE, ADS_TRACK)
    if (context:isCrawl()) then
        context:runAnimation("aim_start_bipod", track, true, PLAY_ONCE_HOLD, 0.2)
    else
        context:runAnimation("aim_start", track, true, PLAY_ONCE_HOLD, 0.2)
    end
    -- 打断检视动画
    context:trigger(this.INPUT_INSPECT_RETREAT)
end

function aiming.update(this, context)
    local track = context:getTrack(BLENDING_TRACK_LINE, ADS_TRACK)
    if (context:isHolding(track)) then
        -- 循环播放瞄准时的动画
        if (context:isCrawl()) then
            context:runAnimation("aim_bipod", track, true, PLAY_ONCE_HOLD, 0.2)
        else
            context:runAnimation("aim", track, true, PLAY_ONCE_HOLD, 0.2)
        end
    end
    -- 当瞄准进度正在减小时转到不瞄准状态，也即取消瞄准
    if (context:getAimingProgress() < this.ADS_states.aiming_progress) then
        context:trigger(this.INPUT_AIM_RETREAT)
    else
        -- 如果没有减小，则记录当前瞄准进度
        this.ADS_states.aiming_progress = context:getAimingProgress()
    end
end

-- 转出瞄准状态
function aiming.transition(this, context, input)
    local track = context:getTrack(BLENDING_TRACK_LINE, ADS_TRACK)
    if (input == this.INPUT_AIM_RETREAT) then
        --播放瞄准结束动画，并调整动画进度使开镜动画与当前的开镜进度相对应
        if (context:isCrawl()) then
            context:runAnimation("aim_end_bipod", track, true, PLAY_ONCE_HOLD, 0.2)
        else
            context:runAnimation("aim_end", track, true, PLAY_ONCE_HOLD, 0.2)
        end
        context:setAnimationProgress(track, 1 - context:getAimingProgress(), true)
        return this.ADS_states.normal
    end
end

function idle_state.transition(this, context, input)
    if (input == INPUT_PUT_AWAY) then
        context:pauseAnimation(context:getTrack(BLENDING_TRACK_LINE, BULLET_TRACK))
        idle_state.empty = -1
    end
    if (input == INPUT_RELOAD) then
        if (isNoAmmo(context)) then
            context:runAnimation("reload_empty", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
        else
            idle_state.empty = context:getCurrentTimestamp()
            if (context:getAmmoCount() > context:getMaxAmmoCount() * (2/3)) then
                context:runAnimation("reload_tactical_1", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            elseif (context:getAmmoCount() > context:getMaxAmmoCount() / 3) then
                context:runAnimation("reload_tactical_2", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("reload_tactical", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        end
        return this.main_track_states.idle
    end
    return main_track_states.idle.transition(this, context, input)
end

local M = setmetatable({
    main_track_states = setmetatable({
        idle = idle_state
    }, {__index = main_track_states}),
    bolt_caught_states = setmetatable({
        bolt_caught = caught_states,
        normal = normal_states
    }, {__index = bolt_caught_states}),
    ADS_states = setmetatable({
        aiming = aiming
    }, {__index = ADS_states}),
    gun_kick_state = gun_kick_state
}, {__index = default})

function M:initialize(context)
    default.initialize(self, context)
end

return M