const { createApp, ref, nextTick } = Vue;

createApp({
    setup() {

        const form = ref({
            departure: '',
            destination: '',
            startDate: '',
            endDate: '',
            people: 1,
            budget: '',
            travelType: '',
            preference: '',
            remark: ''
        });

        const loading = ref(false);
        const showResult = ref(false);
        const guideContent = ref('');
        const chatText = ref('');
        const chatList = ref([]);
        const chatBox = ref(null);

        const scrollChatToBottom = () => {
            nextTick(() => {
                if (chatBox.value) {
                    chatBox.value.scrollTop =
                        chatBox.value.scrollHeight;
                }
            });
        };

        const generateGuide = async () => {

            if (!form.value.departure) {
                alert('请输入出发城市');
                return;
            }

            if (!form.value.destination) {
                alert('请输入目的地');
                return;
            }

            if (!form.value.startDate) {
                alert('请选择出发日期');
                return;
            }

            if (!form.value.endDate) {
                alert('请选择返程日期');
                return;
            }

            if (
                new Date(form.value.endDate) <
                new Date(form.value.startDate)
            ) {
                alert('返程日期不能早于出发日期');
                return;
            }

            loading.value = true;

            try {

                const res = await fetch(
                    '/api/ai/generate-guide',
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(form.value)
                    }
                );

                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }

                const data = await res.json();

                if (data.content) {

                    guideContent.value =
                        marked.parse(data.content);

                    showResult.value = true;

                    nextTick(() => {

                        const resultCard =
                            document.querySelector(
                                '.ai-result-card'
                            );

                        if (resultCard) {
                            window.scrollTo({
                                top: resultCard.offsetTop - 20,
                                behavior: 'smooth'
                            });
                        }

                    });

                } else {

                    alert(
                        '智小策走神了，没能生成攻略，请重试~'
                    );

                }

            } catch (err) {

                console.error(err);

                alert(
                    '网络好像有点问题，请检查后端连接'
                );

            } finally {

                loading.value = false;

            }
        };

        const sendChat = async () => {

            const text = chatText.value.trim();

            if (!text) return;

            chatList.value.push({
                type: 'user',
                content: text
            });

            chatText.value = '';

            scrollChatToBottom();

            try {

                const res = await fetch(
                    '/api/ai/chat',
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            question: text,
                            travelInfo: form.value
                        })
                    }
                );

                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }

                const data = await res.json();

                const answer =
                    data.answer ||
                    '抱歉，智小策暂时无法回答该问题。';

                chatList.value.push({
                    type: 'ai',
                    content: answer,
                    parsedContent: marked.parse(answer)
                });

                scrollChatToBottom();

            } catch (err) {

                console.error(err);

                chatList.value.push({
                    type: 'ai',
                    content: '网络异常',
                    parsedContent:
                        '<p>连接超时，请检查网络连接。</p>'
                });

                scrollChatToBottom();
            }
        };

        const resetPage = () => {

            form.value = {
                departure: '',
                destination: '',
                startDate: '',
                endDate: '',
                people: 1,
                budget: '',
                travelType: '',
                preference: '',
                remark: ''
            };

            showResult.value = false;
            guideContent.value = '';
            chatText.value = '';
            chatList.value = [];
        };

        return {
            form,
            loading,
            showResult,
            guideContent,
            chatText,
            chatList,
            chatBox,
            generateGuide,
            sendChat,
            resetPage
        };
    }
}).mount('#app');