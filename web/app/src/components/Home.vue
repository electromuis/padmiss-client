<template>
    <div id="home" class="row">
        <div class="col-12">
            <h1>Welcome</h1>
            Welcome to the padmiss site! Click around the menu to see whats going on.<br/>
            Want to really join the fun? Go ahead and install: <a href="https://github.com/electromuis/padmiss-daemon/" target="_blank">https://github.com/electromuis/padmiss-daemon/</a> on your SM5 setup :O

            <h1>Cab status</h1>
            <h2 v-if="data === null">Loading ...</h2>
            <table v-else class="table table-striped">
                <tbody>
                    <tr>
                        <td colspan="2"><h2>Info</h2></td>
                    </tr>
                    <tr>
                        <td>Version</td>
                        <td>{{data.info.version}}</td>
                    </tr>
                    <tr>
                        <td colspan="2"><h2>Players</h2></td>
                    </tr>
                    <tr v-if="data.players" v-for="p in [1,2]">
                        <td>Player {{p}}</td>
                        <td v-if="data.players[p] === null">Empty <b-button style="margin-left: 12px;" v-if="$isLoggedIn" @click="logIn(p)">Check in</b-button></td>
                        <td v-else>{{data.players[p].nickname}} <b-button style="margin-left: 12px;" @click="logOut(p)">Log out</b-button></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script>
    import AuthMixin from 'padmiss-client/src/mixins/AuthMixin'

    export default {
        name: "Home",
        mixins: [AuthMixin],

        methods: {
            logIn(side){
                let me = this
                me
                    .$cabClient
                    .post('/check_in', {
                        side: side,
                        player: me.$user.data.playerId
                    })
                    .then(() => me.updatePlayers())
            },

            logOut(side){
                let me = this
                me
                    .$cabClient
                    .post('/check_out', {side: side})
                    .then(() => me.updatePlayers())
            },

            updatePlayers() {
                let me = this

                return me
                    .$cabClient
                    .get('/players')
                    .then(r => {
                        me.data.players = r.players
                        me.$forceUpdate()
                    })
            }
        },

        created() {
            let me = this

            let data = {}

            console.log(this.$cabClient.get('/info'))

            this.$cabClient.get('/info')
                .then(r => {
                    data.info = r
                    me.data = data
                    return me.updatePlayers()
                })
        },

        data() {
            return {
                data: null
            }
        }
    }
</script>

<style scoped>

</style>