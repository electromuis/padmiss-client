<template>
    <div id="home" class="row">
        <div class="col-12">
            <h1>Welcome</h1>
            Welcome to the padmiss site! Click around the menu to see whats going on.<br/>
            Want to really join the fun? Go ahead and install: <a href="https://github.com/electromuis/padmiss-daemon/" target="_blank">https://github.com/electromuis/padmiss-daemon/</a> on your SM5 setup :O

            <h1>Cab status</h1>
            <h2 v-if="data === null">Loading ...</h2>
            <table v-else class="table table-striped">
                <tr>
                    <td>Players 1</td>

                </tr>
            </table>
        </div>
    </div>
</template>

<script>
    export default {
        name: "Home",

        created() {
            this.$cabClient
                .get('/info')
                .then(r => {
                    console.log(r)
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