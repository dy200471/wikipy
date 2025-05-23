之前代码里有段
			// 获取 session
			getSessionAndData(callback) {
				uni.login({
					provider: 'weixin',
					success: (loginRes) => {
						console.log('loginRes:', loginRes.code);
						uni.request({
							url: config.baseUrl + '/code2session',
							method: 'POST',
							data: {
								wxcode: loginRes.code
							},
							success: (sessionRes) => {
								if (sessionRes.data.code === 1) {
									const session = sessionRes.data.data
									console.log('session:', session);
									uni.setStorageSync('session', session);
									if (typeof callback === 'function') {
										callback.call(this, session)
									}
								} else {
									console.log('code2session return error:', sessionRes.data);
								}
							},
							fail: (err) => {
								console.log('code2session failed:', err);
							}
						});
					},
					fail: (err) => {
						console.log('login failed:', err);
					}
				});
			},