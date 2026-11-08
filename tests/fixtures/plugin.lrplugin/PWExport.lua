local LrDialogs = import "LrDialogs"
local logger = import "LrLogger"("TestPlugin")

local function build(n)
  return {
    title = " Export ",
    tooltip = "Starting...",
    label = "Cannot upload - ",
    message = "Uploaded " .. n .. " photos",
    existing = {
      title = LOC "$$$/Test/Export/Existing=Existing label",
    },
  }
end

logger:info("debug message")

LrDialogs.message("Cannot open \"file\"", "Check the path")

--[[ title = "Old label" ]]

return build
