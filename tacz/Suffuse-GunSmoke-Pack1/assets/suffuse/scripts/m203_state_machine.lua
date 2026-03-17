local default = require("tacz_default_state_machine")
local GUN_KICK_TRACK_LINE = default.GUN_KICK_TRACK_LINE
local STATIC_TRACK_LINE = default.STATIC_TRACK_LINE

local BOLT_CAUGHT_TRACK = default.BOLT_CAUGHT_TRACK
local MAIN_TRACK = default.MAIN_TRACK

local main_track_states = default.main_track_states
local base_track_state = default.base_track_state
local bolt_caught_states = default.bolt_caught_states

local gun_kick_state = setmetatable({}, {__index = default.gun_kick_state})
local bolt_caught = setmetatable({}, {__index = bolt_caught_states.bolt_caught})
local normal = setmetatable({}, {__index = bolt_caught_states.normal})

local start_state = setmetatable({}, {__index = main_track_states.start})
local idle_state = setmetatable({}, {__index = main_track_states.idle})

local base_state = {}

local function isNoAmmo(context)
    return (not context:hasBulletInBarrel()) and (context:getAmmoCount() <= 0)
end

local function runPutAwayAnimation(context)
    local put_away_time = context:getPutAwayTime()
    -- 此处获取的轨道是位于主轨道行上的主轨道
    local track = context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK)
    -- 播放 put_away 动画,并且将其过渡时长设为从上下文里传入的 put_away_time * 0.75
    if (context:getAttachment("GRIP") == "tacz:empty") then
        context:runAnimation("put_away", track, false, PLAY_ONCE_HOLD, put_away_time * 0.75)
    else
        context:runAnimation("put_away_grip", track, false, PLAY_ONCE_HOLD, put_away_time * 0.75)
    end
    -- 设定动画进度为最后一帧
    context:setAnimationProgress(track, 1, true)
    -- 将动画进度向前拨动 {put_away_time}
    context:adjustAnimationProgress(track, -put_away_time, false)
end

function base_state.update(this, context)
    if (context:getAttachment("GRIP") == "tacz:empty") then
        context:runAnimation("static_idle", context:getTrack(STATIC_TRACK_LINE, BASE_TRACK), false, LOOP, 0.2)
    else
        context:runAnimation("static_idle_grip", context:getTrack(STATIC_TRACK_LINE, BASE_TRACK), false, LOOP, 0.2)
    end
end

function start_state.transition(this, context, input)
    -- 玩家手里拿到枪的那一瞬间会自动输入一个 draw 的信号,不用手动触发
    if (input == INPUT_DRAW) then
        -- 收到 draw 信号后在主轨道行的主轨道上播放掏枪动画,然后转到闲置态
        this.main_track_states.final.isfinal = -1
        if (context:getAttachment("GRIP") == "tacz:empty") then
            context:runAnimation("draw", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0)
        else
            context:runAnimation("draw_grip", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0)
        end
        return this.main_track_states.idle
    end
end

function idle_state.transition(this, context, input)
    if (input == INPUT_PUT_AWAY) then
        runPutAwayAnimation(context)
        this.main_track_states.final.isfinal = 1
        -- 丢枪后转到最终态
        return this.main_track_states.final
    end
    if (input == INPUT_RELOAD) then
        if (context:getAttachment("GRIP") == "tacz:empty") then
            if (isNoAmmo(context)) then
                context:runAnimation("reload_empty", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("reload_tactical", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        else
            if (isNoAmmo(context)) then
                context:runAnimation("reload_empty_grip", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("reload_tactical_grip", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        end
        return this.main_track_states.idle
    end
    if (input == INPUT_INSPECT) then
        if (context:getAttachment("GRIP") == "tacz:empty") then
            if (isNoAmmo(context)) then
                context:runAnimation("inspect_empty", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("inspect", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        else
            if (isNoAmmo(context)) then
                context:runAnimation("inspect_empty_grip", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("inspect_grip", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        end
        return this.main_track_states.inspect
    end
    return main_track_states.idle.transition(this, context, input)
end

local M = setmetatable({
    main_track_states = setmetatable({
        start = start_state,
        idle = idle_state
    }, {__index = main_track_states}),
    base_track_state = base_state
}, {__index = default})

function M:initialize(context)
    default.initialize(self, context)
end

return M