<template>
        <ol v-if="stack.length > 0" class="breadcrumb">
            <li v-for="s in stack" class="breadcrumb-item" aria-current="page"><a :href="s.url">{{s.meta.title}}</a></li>
        </ol>
</template>

<script>
    export default {
        computed: {
            $stack() {
                let stack = []

                let r = this.$route
                const regex = /\/:(\w+)/gm;

                while(true) {
                    if(!r.meta.parent) {
                        break;
                    }

                    let filtered = this.$router.options.routes.filter(cr => cr.name === r.meta.parent)
                    if(filtered.length === 0) {
                        break;
                    }
                    r = filtered[0]

                    let mt = []
                    let url = "#" + r.path
                    while(mt = regex.exec(r.path)) {
                        if(this.$route.params[mt[1]]) {
                            url = url.replace(':' + mt[1], this.$route.params[mt[1]])
                        }
                    }
                    r.url = url

                    stack.push(r)
                }

                return stack.reverse()
            }
        },

        data() {
            return {
                stack: []
            }
        },

        watch:{
            $route (to, from){
                this.stack = this.$stack
            }
        }
    }
</script>

<style scoped>

</style>