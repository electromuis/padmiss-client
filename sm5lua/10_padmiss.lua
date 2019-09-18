padmiss = {
	url = "https://api.padmiss.com/",
	timeoutSeconds = 2
}

local identifiers = 0

function padmiss.http(url, method, payload, headers)
	identifiers = identifiers + 1

	local jsoni = json.encode({
		url = url,
		identifier = identifiers,
		type = "http",
		method = method,
		payload = payload,
		headers = headers
	})
	
	local util = RageFileUtil.CreateRageFile()
	local path = "/Save/Padmiss/" .. identifiers .. ".jsoni"
	util:Open(path, 2)
	util:Write(jsoni)
	util:Close()
	
	local expect = "/Save/Padmiss/" .. identifiers .. ".jsono"
	local waitUntil = GetTimeSinceStart() + padmiss.timeoutSeconds
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

function padmiss.graph(t, fields, filters)
	local q = "{ " .. t .. " "
	
	if filters ~= nil then
		q = q .. "( "
		
		for k,v in pairs(filters) do
			if k == "queryString" then
				v = json.encode(v)
			end
			
			if type(v) == "string" then
				v = json.encode(v)
			end
		
			q = q .. k .. ": " .. v .. " "
		end
		
		q = q .. ") "
	end
	
	q = q .. "{ " .. fields .. " } }"
	
	local result = padmiss.http(
		padmiss.url .. 'graphiql',
		'POST',
		json.encode({
			query = q
		}),
		{
			["Content-Type"] = "application/json"
		}
	)
	
	if result == false or string.len(result) == 0 then
		return false
	end
	
	local result = json.decode(result)
	
	if result['data'] == nil or result['data'][t] == nil then
		return false
	end
	
	return result['data'][t]
end

function padmiss.song_highscores(song)
	local result = padmiss.graph(
		'Stepcharts',
		'docs { _id }',
		{ queryString = {
			['song.title'] = song:GetDisplayMainTitle(),
			['song.artist'] = song:GetDisplayArtist()
		} }
	)
	
	if result == false or #result['docs'] == 0 then
		return {}
	end
	
	local ids = {}
	for k,v in pairs(result['docs']) do
		ids[#ids+1] = v._id
	end
	
	result = padmiss.graph(
		'Scores',
		'docs { player { nickname } }',
		{
			queryString = {
				stepChart = ids
			},
			limit = 100,
			sort = "scoreValue"
		}
	)
	
	if result == false or #result['docs'] == 0 then
		return {}
	end
	
	return result['docs']
end

--EXAMPLE START--
--song = SONGMAN:FindSong('Springtime')
--scores = padmiss.song_highscores(song)

--for k,s in pairs(scores) do
	--t[#t+1] = Def.BitmapText{
		--Font="Common normal",
		--Text=s.player.nickname
	--}
--end
--EXAMPLE END--

return padmiss