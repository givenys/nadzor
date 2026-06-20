import Home from '../pages/Home';
import Nadzor from '../pages/Nadzor';
import Cams from '../pages/Cams';
import Test from '../pages/Test';

import Auth from '../pages/Auth';
import NotFoundPage from '../pages/NotFoundPage';

export const page_routes = [

    {   path: '/', 
        label: '',//'Главная',                          
        props: {}, 
        component: Home
    },

    {   path: '/nadzor',  
        label: 'Надзор', 
        props: {}, 
        component: Nadzor,
        protected: true,
        adminOnly: true
    },

    {   
        path: '/Cams',
        label: 'Камеры',
        props: {},
        component: Cams,
        protected: true,
        adminOnly: true
    },

    {   
        path: '/Test',
        label: 'Настройки',
        props: {},
        component: Test,
        protected: true,
        adminOnly: true
    },


    {   path: '/auth',  
        label: 'Авторизация', 
        props: {
            override_styles: ['nav-link-right', 'auth-btn']
        },      
        component: Auth 
    }, 


    // Must be last 

    {   path: '*',  
        label: '',
        props: {},               
        component: NotFoundPage 
    },


];
