padmiss = {
	url = "https://api.padmiss.com/"
}

local identifiers = 0

function padmiss.http(url, method, payload)
	identifiers = identifiers + 1

	local jsoni = json.encode({
		url = url,
		identifier = identifiers,
		type = "http",
		method = method,
		payload = payload
	})
	
	local util = RageFileUtil.CreateRageFile()
	local path = "/Save/Padmiss/" .. identifiers .. ".jsoni"
	util:Open(path, 2)
	util:Write(jsoni)
	util:Close()
	
	local expect = "/Save/Padmiss/" .. identifiers .. ".jsono"
	local waitUntil = GetTimeSinceStart() + 10
	local check = false
	
	while check == false do
		if GetTimeSinceStart() > waitUntil then
			lua.ReportScriptError("Timeout")
			util:Close()
			return false
		end
		
		check = util:Open(expect, 1)
	
		local wait = GetTimeSinceStart() + 0.5
		
		while GetTimeSinceStart() < wait do
			--
		end
		
		lua.ReportScriptError("Checking for: " .. expect)
	end
	
	util:Open(expect, 1)
	local response = util:Read()
	util:Close()
	return response
end

function padmiss.graph(t, req)
	local request = {
		query = [[{Players {docs {nickname}}}]]
	}
	
	local result = padmiss.http(
		padmiss.url .. 'graphiql',
		'POST',
		json.encode(request)
	)
	
	if string.len(result) == 0 then
		return false
	end
	
	result = json.decode(result)
	
	return result
end

lua.ReportScriptError(padmiss.graph('Players', 'asd'))

return padmiss