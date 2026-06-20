import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { page_routes } from './config/page_routes';

import Header from './components/Header';
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'

import './App.css'

function App() {

    return (
        <Router>

            <Header />

            <main className='App-main'>
                <Routes>
                    { page_routes.map((r) => {

                        const element = r.protected
                            ? <ProtectedRoute adminOnly={r.adminOnly}>{<r.component {...r.props} />}</ProtectedRoute>
                            : <r.component {...r.props} />;

                        return (
                            <Route key={r.path} path={r.path} element={element} />
                        );
                    })}
                </Routes>
            </main>

            <Footer />

        </Router>

    );

};

export default App;
